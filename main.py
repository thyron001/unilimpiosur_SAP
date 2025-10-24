# main.py — limpio, usando procesamiento_pedidos.py

import os
from datetime import datetime
from decimal import Decimal
import bcrypt
from functools import wraps

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

import psycopg
from threading import Thread
from flask import Flask, render_template, jsonify, abort, session, redirect, url_for, request as flask_request
from flask import request

import subir_datos as subir
import escucha_correos                  # escucha IMAP (módulo en español)
import procesamiento_pedidos as proc    # parseo + emparejado
import persistencia_postgresql as db


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-por-defecto-cambiar-en-produccion')

# Configurar sesión para que expire en 8 horas
from datetime import timedelta
app.permanent_session_lifetime = timedelta(hours=8)

# ========= UTILIDADES DE PERSISTENCIA (quedan aquí) =========

def a_decimal(valor) -> Decimal | None:
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

# ========= SISTEMA DE AUTENTICACIÓN =========

def verificar_usuario(username: str, password: str) -> dict | None:
    """Verifica las credenciales del usuario y devuelve los datos del usuario si son válidas"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, password_hash, nombre_completo, email
                FROM usuarios 
                WHERE username = %s AND activo = TRUE
            """, (username,))
            row = cur.fetchone()
            
            if row:
                user_id, username_db, password_hash, nombre_completo, email = row
                # Verificar la contraseña usando bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    # Actualizar último acceso
                    cur.execute("""
                        UPDATE usuarios 
                        SET ultimo_acceso = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    """, (user_id,))
                    conn.commit()
                    
                    return {
                        'id': user_id,
                        'username': username_db,
                        'nombre_completo': nombre_completo,
                        'email': email
                    }
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
    
    return None

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Si la sesión expiró, redirigir al login con mensaje
            return redirect(url_for('login', expired='true'))
        return f(*args, **kwargs)
    return decorated_function

def login_user(user_data: dict):
    """Inicia sesión para el usuario"""
    session.permanent = True  # Marcar sesión como permanente para que use el tiempo de vida configurado
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['nombre_completo'] = user_data['nombre_completo']
    session['email'] = user_data['email']

def logout_user():
    """Cierra la sesión del usuario"""
    session.clear()

def obtener_saludo_aleatorio(nombre_usuario: str) -> str:
    """Genera un saludo aleatorio con el nombre del usuario"""
    import random
    
    frases_saludo = [
        "Bienvenido",
        "¡Hola",
        "¡Qué tal",
        "¡Saludos",
        "¡Buenos días",
        "¡Buenas tardes",
        "¡Buenas noches",
        "¡Encantado de verte",
        "¡Es un placer verte",
        "¡Qué gusto verte"
    ]
    
    frase = random.choice(frases_saludo)
    return f"{frase} {nombre_usuario}!"



# ========= CALLBACK DEL ESCUCHADOR =========

def al_encontrar_pdf(meta: dict, nombre_pdf: str, pdf_en_bytes: bytes) -> None:
    print("\n=== 📬 Nuevo correo (callback Flask) ===")
    print(f"De:      {meta.get('remitente','')}")
    print(f"Asunto:  {meta.get('asunto','')}")
    print(f"Fecha:   {meta.get('fecha')}")
    print(f"UID:     {meta.get('uid')}")
    print(f"📎 PDF:  {nombre_pdf}")

    # Procesar todos los correos sin restricciones temporales
    uid_correo = meta.get("uid")
    print(f"📧 Procesando correo UID {uid_correo} desde aplicación Flask")

    # 1) Filas de la tabla
    filas = proc.extraer_filas_pdf(pdf_en_bytes)
    if not filas:
        print("[WARNING] No se detectaron filas en el PDF.")
        return

    # 2) Sucursal (del PDF)
    resumen = proc.extraer_sucursal(pdf_en_bytes)

    # 3) Emparejar contra BD (cliente fijo: Roldan), usando el alias, RUC y encargado de sucursal del PDF
    filas_enriquecidas, suc, cliente_id = proc.emparejar_filas_con_bd(
        filas,
        cliente_nombre="Roldan",
        sucursal_alias=resumen.get("sucursal"),
        sucursal_ruc=resumen.get("ruc"),
        sucursal_encargado=resumen.get("encargado")
    )

    # 4) Verificar si se encontró la sucursal por alias
    sucursal_alias_pdf = resumen.get("sucursal")
    if sucursal_alias_pdf and not suc:
        # No se encontró coincidencia en el alias - marcar como error
        print(f"[ERROR] No se encontró sucursal con alias '{sucursal_alias_pdf}' en la base de datos")
        pedido = {
            "fecha": meta.get("fecha"),
            "sucursal": f"ERROR: Alias '{sucursal_alias_pdf}' no encontrado",
            "orden_compra": resumen.get("orden_compra"),  # número de orden de compra del PDF
        }
        try:
            pedido_id, numero_pedido, estado = db.guardar_pedido(pedido, filas_enriquecidas, cliente_id, None)
            print(f"[WARNING] Pedido guardado con ERROR: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
        except Exception as e:
            print(f"[ERROR] No se guardó el pedido con error: {e}")
        return

    # 5) Armar dict 'pedido' para persistencia_postgresql.guardar_pedido()
    pedido = {
        "fecha": meta.get("fecha"),
        "sucursal": suc.get("nombre") if suc else "SUCURSAL DESCONOCIDA",  # nombre del sistema si se encontró
        "orden_compra": resumen.get("orden_compra"),  # número de orden de compra del PDF
    }

    # 6) Guardar en PostgreSQL (usa tu función existente)
    try:
        sucursal_id = suc.get("id") if suc else None
        pedido_id, numero_pedido, estado = db.guardar_pedido(pedido, filas_enriquecidas, cliente_id, sucursal_id)
        print(f"✅ [Flask] Pedido guardado exitosamente: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
    except Exception as e:
        print(f"❌ [Flask] Error al guardar el pedido: {e}")
        return

    # (opcional) logs en terminal
    proc.imprimir_filas_emparejadas(filas_enriquecidas)



# ========= RUTAS FLASK =========

@app.route("/")
def index():
    """Redirige a la página de pedidos"""
    from flask import redirect, url_for
    return redirect(url_for('ver_pedidos'))

# ========= RUTAS DE AUTENTICACIÓN =========

@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            return render_template("login.html", error="Por favor, complete todos los campos")
        
        user_data = verificar_usuario(username, password)
        if user_data:
            login_user(user_data)
            # Generar saludo aleatorio y guardarlo en la sesión
            saludo = obtener_saludo_aleatorio(user_data['nombre_completo'])
            session['saludo'] = saludo
            # Redirigir a la página que intentaba acceder o a pedidos por defecto
            next_page = request.args.get('next')
            return redirect(next_page or url_for('ver_pedidos'))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
    
    # Verificar si la sesión expiró
    expired = request.args.get('expired')
    error_message = None
    if expired == 'true':
        error_message = "Su sesión ha expirado. Por favor, inicie sesión nuevamente."
    
    return render_template("login.html", error=error_message)

@app.route("/logout")
def logout():
    """Cerrar sesión"""
    logout_user()
    return redirect(url_for('login'))

@app.route("/pedidos")
@login_required
def ver_pedidos():
    # Por defecto mostrar pedidos por procesar
    estado = request.args.get('estado', 'por_procesar')
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, numero_pedido, fecha, sucursal, estado
            FROM pedidos
            WHERE estado = %s
            ORDER BY id DESC
            LIMIT 200;
        """, (estado,))
        filas = [
            {"id": i, "numero_pedido": n, "fecha": f, "sucursal": s, "estado": e}
            for (i, n, f, s, e) in cur.fetchall()
        ]
    return render_template("orders.html", orders=filas, estado_actual=estado, now=datetime.utcnow())


@app.route("/clientes")
@login_required
def vista_clientes():
    return render_template("clientes.html")

@app.route("/api/clientes")
@login_required
def api_clientes():
    """Obtiene lista de clientes para filtros"""
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        # Verificar si la columna activo existe
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clientes' AND column_name = 'activo';
        """)
        tiene_columna_activo = cur.fetchone() is not None
        
        if tiene_columna_activo:
            cur.execute("""
                SELECT id, nombre, ruc
                FROM clientes
                WHERE activo = TRUE
                ORDER BY upper(nombre);
            """)
        else:
            cur.execute("""
                SELECT id, nombre, ruc
                FROM clientes
                ORDER BY upper(nombre);
            """)
        
        clientes = [
            {"id": cid, "nombre": nom, "ruc": ruc}
            for (cid, nom, ruc) in cur.fetchall()
        ]
    return jsonify({"clientes": clientes})

@app.route("/api/clientes_con_sucursales")
@login_required
def api_clientes_con_sucursales():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.usa_bodega_por_sucursal, 
                   c.alias_por_sucursal, c.alias_por_producto,
                   c.ruc_por_sucursal
            FROM clientes c
            ORDER BY upper(c.nombre);
        """)
        clientes = [
            {
                "id": cid, "nombre": nom, "ruc": ruc,
                "usa_bodega_por_sucursal": bool(ubs),
                "alias_por_sucursal": bool(alias_suc),
                "alias_por_producto": bool(alias_prod),
                "ruc_por_sucursal": bool(ruc_por_suc),
                "sucursales": []
            }
            for (cid, nom, ruc, ubs, alias_suc, alias_prod, ruc_por_suc) in cur.fetchall()
        ]
        idx = {c["id"]: c for c in clientes}

        if clientes:
            cur.execute("""
                SELECT s.id, s.cliente_id, s.alias, s.nombre, s.encargado, s.direccion, s.activo, s.ruc, s.ciudad
                FROM sucursales s
                WHERE s.activo = TRUE
                ORDER BY upper(s.nombre);
            """)
            for (sid, cliente_id, alias, nombre, encargado, direccion, activo, ruc, ciudad) in cur.fetchall():
                if cliente_id in idx:
                    idx[cliente_id]["sucursales"].append({
                        "id": sid, "alias": alias, "nombre": nombre,
                        "encargado": encargado, "direccion": direccion, "ruc": ruc, "ciudad": ciudad
                    })

    return jsonify(list(idx.values()))


@app.route("/api/clientes/<int:cliente_id>", methods=["PUT"])
@login_required
def api_actualizar_cliente(cliente_id):
    data = request.get_json(silent=True) or {}
    
    # Validar datos requeridos
    nombre = data.get("nombre", "").strip()
    ruc = data.get("ruc", "").strip()
    
    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400
    if not ruc:
        return jsonify({"ok": False, "error": "El RUC es obligatorio"}), 400
    
    # Validar RUC (debe tener entre 10 y 13 dígitos)
    ruc_digits = ''.join(filter(str.isdigit, ruc))
    if len(ruc_digits) < 10 or len(ruc_digits) > 13:
        return jsonify({"ok": False, "error": "El RUC debe tener entre 10 y 13 dígitos"}), 400
    
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el cliente existe
            cur.execute("SELECT id FROM clientes WHERE id = %s", (cliente_id,))
            if not cur.fetchone():
                return jsonify({"ok": False, "error": "Cliente no encontrado"}), 404
            
            # Verificar que el RUC no esté en uso por otro cliente
            cur.execute("SELECT id FROM clientes WHERE ruc = %s AND id != %s", (ruc, cliente_id))
            if cur.fetchone():
                return jsonify({"ok": False, "error": "El RUC ya está en uso por otro cliente"}), 400
            
            # Actualizar cliente
            cur.execute("""
                UPDATE clientes 
                SET 
                    nombre = %s,
                    ruc = %s,
                    usa_bodega_por_sucursal = %s,
                    alias_por_sucursal = %s,
                    alias_por_producto = %s,
                    ruc_por_sucursal = %s
                WHERE id = %s
            """, (
                nombre,
                ruc,
                data.get("usa_bodega_por_sucursal", False),
                data.get("alias_por_sucursal", False),
                data.get("alias_por_producto", False),
                data.get("ruc_por_sucursal", False),
                cliente_id
            ))
            
            conn.commit()
            
        return jsonify({"ok": True, "mensaje": "Cliente actualizado correctamente"})
        
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        return jsonify({"ok": False, "error": "Error interno del servidor"}), 500


@app.route("/api/sucursales/bulk", methods=["POST"])
@login_required
def api_sucursales_bulk():
    data = request.get_json(silent=True) or {}
    cambios = data.get("cambios") or []
    if not isinstance(cambios, list):
        return jsonify({"ok": False, "error": "Formato inválido"}), 400

    resultados = {"insertados": 0, "actualizados": 0, "borrados": 0}

    with db.obtener_conexion() as conn, conn.cursor() as cur:
        for c in cambios:
            cliente_id  = c.get("cliente_id")
            sucursal_id = c.get("sucursal_id")
            nombre      = (c.get("nombre") or "").strip()
            alias       = (c.get("alias") or "").strip() or None
            encargado   = (c.get("encargado") or "").strip() or None
            direccion   = (c.get("direccion") or "").strip() or None
            ruc         = (c.get("ruc") or "").strip() or None
            ciudad      = (c.get("ciudad") or "").strip() or None
            borrar      = bool(c.get("borrar"))

            if borrar and sucursal_id:
                cur.execute("DELETE FROM sucursales WHERE id = %s;", (sucursal_id,))
                resultados["borrados"] += 1
                continue

            if not nombre:
                # ignorar filas sin nombre (regla del front)
                continue

            if sucursal_id:
                cur.execute("""
                    UPDATE sucursales
                       SET nombre = %s, alias = %s, encargado = %s, direccion = %s, ruc = %s, ciudad = %s
                     WHERE id = %s;
                """, (nombre, alias, encargado, direccion, ruc, ciudad, sucursal_id))
                resultados["actualizados"] += (cur.rowcount or 0)
            else:
                cur.execute("""
                    INSERT INTO sucursales (cliente_id, nombre, alias, encargado, direccion, ruc, ciudad, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id;
                """, (cliente_id, nombre, alias, encargado, direccion, ruc, ciudad))
                nuevo_id = cur.fetchone()[0]
                resultados["insertados"] += 1

    return jsonify({"ok": True, **resultados})


# === VISTA HTML ===
@app.route("/productos")
@login_required
def vista_productos():
    return render_template("productos.html")


# === CATÁLOGO DE PRODUCTOS (SKU/NOMBRE) PARA DATALIST ===
@app.route("/api/productos_catalogo")
def api_productos_catalogo():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT sku, nombre
            FROM productos
            WHERE activo = TRUE
            ORDER BY upper(nombre);
        """)
        data = [{"sku": s or "", "nombre": n or ""} for (s, n) in cur.fetchall()]
    return jsonify(data)


# === LISTA UNIFICADA DE MAPEOS (POR CLIENTE y POR SUCURSAL+CLIENTE) ===
@app.route("/api/productos_mapeos")
def api_productos_mapeos():
    result = {"por_cliente": [], "por_sucursal": []}
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        # ------- POR CLIENTE -------
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.alias_por_producto
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = FALSE
            ORDER BY upper(c.nombre);
        """)
        clientes_pc = [{"id": i, "nombre": n, "ruc": r, "alias_por_producto": ap} for (i,n,r,ap) in cur.fetchall()]
        idmap = {c["id"]: c for c in clientes_pc}

        por_cliente = {}
        if clientes_pc:
            cur.execute("""
                SELECT bpc.id, bpc.cliente_id, p.id, p.sku, p.nombre, bpc.bodega
                FROM bodegas_producto_por_cliente bpc
                JOIN productos p ON p.id = bpc.producto_id
                ORDER BY bpc.cliente_id, upper(p.nombre);
            """)
            for (mapeo_id, cliente_id, pid, sku, pnom, bodega) in cur.fetchall():
                # Construir objeto sin alias (los alias se gestionan en el modal)
                fila = {
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                }
                
                por_cliente.setdefault(cliente_id, []).append(fila)
        for cid, cli in idmap.items():
            result["por_cliente"].append({
                "cliente": cli,
                "filas": por_cliente.get(cid, [])
            })


        # ------- POR SUCURSAL + CLIENTE -------
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.alias_por_producto
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = TRUE
            ORDER BY upper(c.nombre);
        """)
        clientes_ps = [{"id": i, "nombre": n, "ruc": r, "alias_por_producto": ap} for (i,n,r,ap) in cur.fetchall()]

        if clientes_ps:
            # 1) sucursales activas
            cur.execute("""
                SELECT s.id, s.cliente_id, s.nombre
                FROM sucursales s
                WHERE s.activo = TRUE
                AND s.cliente_id = ANY(%s)
                ORDER BY s.cliente_id, upper(s.nombre);
            """, ([c["id"] for c in clientes_ps],))
            por_cliente = {}
            for (suc_id, cli_id, suc_nombre) in cur.fetchall():
                por_cliente.setdefault(cli_id, {})
                por_cliente[cli_id].setdefault(suc_id, {
                    "sucursal": {"id": suc_id, "nombre": suc_nombre},
                    "filas": []
                })

            # 2) mapeos existentes
            cur.execute("""
                SELECT bps.id, s.id, s.cliente_id, s.nombre,
                    p.id, p.sku, p.nombre, bps.bodega
                FROM bodegas_producto_por_sucursal bps
                JOIN sucursales s ON s.id = bps.sucursal_id
                JOIN productos p  ON p.id = bps.producto_id
                WHERE s.activo = TRUE
                AND s.cliente_id = ANY(%s)
                ORDER BY s.cliente_id, upper(s.nombre), upper(p.nombre);
            """, ([c["id"] for c in clientes_ps],))
            for (mapeo_id, suc_id, cli_id, suc_nombre, pid, sku, pnom, bodega) in cur.fetchall():
                por_cliente.setdefault(cli_id, {})
                por_cliente[cli_id].setdefault(suc_id, {
                    "sucursal": {"id": suc_id, "nombre": suc_nombre},
                    "filas": []
                })
                
                # Construir objeto sin alias (los alias se gestionan en el modal)
                fila = {
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                }
                
                por_cliente[cli_id][suc_id]["filas"].append(fila)

            for cli in clientes_ps:
                bloques = list(por_cliente.get(cli["id"], {}).values())
                result["por_sucursal"].append({
                    "cliente": cli,
                    "bloques": bloques
                })




    return jsonify(result)


@app.route("/api/productos_por_cliente/bulk", methods=["POST"])
def api_productos_por_cliente_bulk():
    from flask import request, jsonify
    data = request.get_json(silent=True) or {}
    cambios = data.get("cambios") or []
    if not isinstance(cambios, list):
        return jsonify({"ok": False, "error": "Formato inválido"}), 400

    res = {"insertados": 0, "actualizados": 0, "borrados": 0, "productos_creados": 0}

    with db.obtener_conexion() as conn, conn.cursor() as cur:
        for c in cambios:
            cliente_id   = c.get("cliente_id")
            mapeo_id     = c.get("mapeo_id")
            producto_id_existente = c.get("producto_id")
            sku          = (c.get("producto_sku") or "").strip() or None
            nombre_prod  = (c.get("producto_nombre") or "").strip() or None
            bodega       = (c.get("bodega") or "").strip() or None
            borrar       = bool(c.get("borrar"))

            if borrar and mapeo_id:
                cur.execute("DELETE FROM bodegas_producto_por_cliente WHERE id = %s;", (mapeo_id,))
                res["borrados"] += 1
                continue

            if not sku and not nombre_prod:
                continue  # necesita al menos algo

            # Asegurar producto - permite SKUs duplicados con diferentes nombres
            producto_id = producto_id_existente
            
            # Si no tenemos producto_id existente, buscar/crear producto
            if not producto_id:
                # Si hay SKU y nombre, buscar por ambos para evitar duplicados exactos
                if sku and nombre_prod:
                    cur.execute("SELECT id FROM productos WHERE sku = %s AND upper(nombre) = upper(%s);", (sku, nombre_prod))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Si solo hay SKU, buscar el primer producto con ese SKU
                elif sku:
                    cur.execute("SELECT id FROM productos WHERE sku = %s LIMIT 1;", (sku,))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Si solo hay nombre, buscar por nombre exacto
                elif nombre_prod:
                    cur.execute("SELECT id FROM productos WHERE upper(nombre) = upper(%s) LIMIT 1;", (nombre_prod,))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Crear nuevo producto si no existe
                if not producto_id:
                    cur.execute("""
                        INSERT INTO productos (sku, nombre, activo) VALUES (%s, %s, TRUE)
                        RETURNING id;
                    """, (sku or "", nombre_prod or ""))
                    producto_id = cur.fetchone()[0]
                    res["productos_creados"] += 1

            # Upsert bodega por cliente
            if mapeo_id:
                # Usar una sola operación que maneje todos los casos
                # Primero eliminar el registro actual si existe
                cur.execute("DELETE FROM bodegas_producto_por_cliente WHERE id = %s;", (mapeo_id,))
                
                # Luego insertar el nuevo registro (puede ser el mismo producto_id o uno diferente)
                cur.execute("""
                    INSERT INTO bodegas_producto_por_cliente (cliente_id, producto_id, bodega)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (cliente_id, producto_id) 
                    DO UPDATE SET bodega = EXCLUDED.bodega
                    RETURNING id;
                """, (cliente_id, producto_id, bodega))
                _ = cur.fetchone()[0]
                res["actualizados"] += 1
            else:
                # Usar INSERT ... ON CONFLICT para manejar duplicados
                cur.execute("""
                    INSERT INTO bodegas_producto_por_cliente (cliente_id, producto_id, bodega)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (cliente_id, producto_id) 
                    DO UPDATE SET bodega = EXCLUDED.bodega
                    RETURNING id;
                """, (cliente_id, producto_id, bodega))
                _ = cur.fetchone()[0]
                res["insertados"] += 1
            
            # Los alias ahora se gestionan desde el modal de alias en el frontend

    return jsonify({"ok": True, **res})


# === GUARDADO BULK: POR SUCURSAL ===
@app.route("/api/productos_por_sucursal/bulk", methods=["POST"])
def api_productos_por_sucursal_bulk():
    from flask import request, jsonify
    data = request.get_json(silent=True) or {}
    cambios = data.get("cambios") or []
    if not isinstance(cambios, list):
        return jsonify({"ok": False, "error": "Formato inválido"}), 400

    res = {"insertados": 0, "actualizados": 0, "borrados": 0, "productos_creados": 0}

    with db.obtener_conexion() as conn, conn.cursor() as cur:
        for c in cambios:
            sucursal_id  = c.get("sucursal_id")
            mapeo_id     = c.get("mapeo_id")
            producto_id_existente = c.get("producto_id")
            sku          = (c.get("producto_sku") or "").strip() or None
            nombre_prod  = (c.get("producto_nombre") or "").strip() or None
            bodega       = (c.get("bodega") or "").strip() or None
            borrar       = bool(c.get("borrar"))

            if borrar and mapeo_id:
                cur.execute("DELETE FROM bodegas_producto_por_sucursal WHERE id = %s;", (mapeo_id,))
                res["borrados"] += 1
                continue

            if not sku and not nombre_prod:
                continue

            # Asegurar producto - permite SKUs duplicados con diferentes nombres
            producto_id = producto_id_existente
            
            # Si no tenemos producto_id existente, buscar/crear producto
            if not producto_id:
                # Si hay SKU y nombre, buscar por ambos para evitar duplicados exactos
                if sku and nombre_prod:
                    cur.execute("SELECT id FROM productos WHERE sku = %s AND upper(nombre) = upper(%s);", (sku, nombre_prod))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Si solo hay SKU, buscar el primer producto con ese SKU
                elif sku:
                    cur.execute("SELECT id FROM productos WHERE sku = %s LIMIT 1;", (sku,))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Si solo hay nombre, buscar por nombre exacto
                elif nombre_prod:
                    cur.execute("SELECT id FROM productos WHERE upper(nombre) = upper(%s) LIMIT 1;", (nombre_prod,))
                    r = cur.fetchone()
                    if r: producto_id = r[0]
                
                # Crear nuevo producto si no existe
                if not producto_id:
                    cur.execute("""
                        INSERT INTO productos (sku, nombre, activo) VALUES (%s, %s, TRUE)
                        RETURNING id;
                    """, (sku or "", nombre_prod or ""))
                    producto_id = cur.fetchone()[0]
                    res["productos_creados"] += 1

            # Upsert bodega por sucursal
            if mapeo_id:
                cur.execute("""
                    UPDATE bodegas_producto_por_sucursal
                       SET producto_id = %s, bodega = %s
                     WHERE id = %s;
                """, (producto_id, bodega, mapeo_id))
                res["actualizados"] += (cur.rowcount or 0)
            else:
                cur.execute("""
                    INSERT INTO bodegas_producto_por_sucursal (sucursal_id, producto_id, bodega)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (sucursal_id, producto_id, bodega))
                _ = cur.fetchone()[0]
                res["insertados"] += 1
            
            # Los alias ahora se gestionan desde el modal de alias en el frontend

    return jsonify({"ok": True, **res})






@app.route("/api/orders/summary")
def resumen_pedidos():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos;")
        (cantidad,) = cur.fetchone()
    return jsonify({"count": int(cantidad)})

@app.route("/api/pedidos/por_estado/<estado>")
def api_pedidos_por_estado(estado: str):
    """Obtiene pedidos filtrados por estado"""
    estados_validos = ['por_procesar', 'procesado', 'con_errores']
    if estado not in estados_validos:
        return jsonify({"error": "Estado inválido"}), 400
    
    # Obtener parámetros de filtro de la query string
    cliente_id = request.args.get('cliente_id', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        # Construir query base
        query = """
            SELECT p.id, p.numero_pedido, p.fecha, p.sucursal, p.estado, c.nombre as cliente_nombre
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            WHERE p.estado = %s
        """
        params = [estado]
        
        # Agregar filtros opcionales
        if cliente_id:
            query += " AND p.cliente_id = %s"
            params.append(cliente_id)
        
        if fecha_desde:
            query += " AND p.fecha >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND p.fecha <= %s"
            params.append(fecha_hasta)
        
        query += " ORDER BY p.id DESC LIMIT 200;"
        
        cur.execute(query, params)
        filas = [
            {"id": i, "numero_pedido": n, "fecha": f, "sucursal": s, "estado": e, "cliente_nombre": cn}
            for (i, n, f, s, e, cn) in cur.fetchall()
        ]
    return jsonify({"pedidos": filas, "estado": estado})

@app.route("/api/generar_sap", methods=["POST"])
@login_required
def api_generar_sap():
    """Genera archivos SAP para pedidos seleccionados o todos los por procesar"""
    try:
        import generador_sap
        import tempfile
        import os
        from flask import send_file
        from datetime import datetime
        
        # Obtener datos del request
        data = request.get_json() or {}
        pedidos_ids = data.get('pedidos_ids', [])
        tipo_archivo = data.get('tipo_archivo')  # 'odrf' o 'drf1'
        
        # Si no se especifican pedidos, usar todos los por procesar
        if not pedidos_ids:
            odrf_path, drf1_path = generador_sap.generar_archivos_sap()
        else:
            # Generar archivos solo para los pedidos seleccionados
            odrf_path, drf1_path = generador_sap.generar_archivos_sap_por_ids(pedidos_ids)
        
        if odrf_path and drf1_path:
            # Si se especifica un tipo de archivo, devolver solo ese archivo
            if tipo_archivo == 'odrf':
                return send_file(odrf_path, as_attachment=True, download_name=f"ODRF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            elif tipo_archivo == 'drf1':
                return send_file(drf1_path, as_attachment=True, download_name=f"DRF1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            else:
                # Devolver información de los archivos generados
                return jsonify({
                    "ok": True,
                    "mensaje": "Archivos SAP generados exitosamente",
                    "archivos": {
                        "odrf": odrf_path,
                        "drf1": drf1_path
                    }
                })
        else:
            return jsonify({
                "ok": False,
                "mensaje": "No hay pedidos seleccionados para generar archivos SAP"
            })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

# Variable global para almacenar archivos temporales generados
archivos_sap_temporales = {}

@app.route("/api/generar_sap_completo", methods=["POST"])
@login_required
def api_generar_sap_completo():
    """Genera ambos archivos SAP y los almacena temporalmente para descarga"""
    try:
        import generador_sap
        from datetime import datetime
        import uuid
        
        # Obtener datos del request
        data = request.get_json() or {}
        pedidos_ids = data.get('pedidos_ids', [])
        
        # Generar ID único para esta sesión de descarga
        session_id = str(uuid.uuid4())
        
        # Si no se especifican pedidos, usar todos los por procesar
        if not pedidos_ids:
            odrf_path, drf1_path = generador_sap.generar_archivos_sap()
        else:
            # Generar archivos solo para los pedidos seleccionados
            odrf_path, drf1_path = generador_sap.generar_archivos_sap_por_ids(pedidos_ids)
        
        if odrf_path and drf1_path:
            # Almacenar rutas de archivos temporalmente
            archivos_sap_temporales[session_id] = {
                'odrf': odrf_path,
                'drf1': drf1_path,
                'timestamp': datetime.now()
            }
            
            return jsonify({
                "ok": True,
                "mensaje": "Archivos SAP generados exitosamente",
                "session_id": session_id
            })
        else:
            return jsonify({
                "ok": False,
                "mensaje": "No hay pedidos seleccionados para generar archivos SAP"
            }), 400
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/api/descargar_sap/<tipo_archivo>", methods=["POST"])
@login_required
def api_descargar_sap(tipo_archivo):
    """Descarga un archivo SAP específico (odrf o drf1) usando session_id"""
    try:
        from flask import send_file
        from datetime import datetime
        
        # Obtener datos del request
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        # Validar tipo de archivo
        if tipo_archivo not in ['odrf', 'drf1']:
            return jsonify({
                "ok": False,
                "error": "Tipo de archivo inválido. Use 'odrf' o 'drf1'"
            }), 400
        
        # Validar session_id
        if not session_id or session_id not in archivos_sap_temporales:
            return jsonify({
                "ok": False,
                "error": "Sesión de descarga inválida o expirada"
            }), 400
        
        # Obtener rutas de archivos
        archivos = archivos_sap_temporales[session_id]
        archivo_path = archivos[tipo_archivo]
        
        if not os.path.exists(archivo_path):
            return jsonify({
                "ok": False,
                "error": f"Archivo {tipo_archivo.upper()} no encontrado"
            }), 404
        
        # Generar nombre de archivo
        timestamp = archivos['timestamp'].strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"{tipo_archivo.upper()}_{timestamp}.txt"
        
        # Enviar archivo
        response = send_file(archivo_path, as_attachment=True, download_name=nombre_archivo)
        
        # Si es el segundo archivo (DRF1), limpiar ambos archivos
        if tipo_archivo == 'drf1':
            try:
                if os.path.exists(archivos['odrf']):
                    os.remove(archivos['odrf'])
                if os.path.exists(archivos['drf1']):
                    os.remove(archivos['drf1'])
                # Eliminar entrada de la sesión
                del archivos_sap_temporales[session_id]
            except Exception as e:
                print(f"Warning: No se pudieron limpiar archivos temporales: {e}")
        
        return response
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ====== DETALLE PEDIDO =======
@app.route("/api/pedidos/<int:pedido_id>")
def api_detalle_pedido(pedido_id: int):
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
                p.numero_pedido, 
                p.fecha, 
                p.sucursal, 
                p.cliente_id, 
                p.sucursal_id,
                p.orden_compra,
                c.nombre as cliente_nombre,
                c.ruc as cliente_ruc,
                s.nombre as sucursal_nombre,
                s.encargado,
                s.ruc as sucursal_ruc
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN sucursales s ON s.id = p.sucursal_id
            WHERE p.id = %s;
        """, (pedido_id,))
        row = cur.fetchone()
        if not row:
            return abort(404)

        (numero_pedido, fecha, sucursal, cliente_id, sucursal_id, orden_compra,
         cliente_nombre, cliente_ruc, sucursal_nombre, encargado, sucursal_ruc) = row

        cur.execute("""
            SELECT descripcion, sku, bodega, cantidad
            FROM pedido_items
            WHERE pedido_id = %s
            ORDER BY id ASC;
        """, (pedido_id,))
        items = [
            {
                "descripcion": d or "",
                "sku": s or "",
                "bodega": b or "",
                "cantidad": int(c or 0),
                "tiene_error": not s or not b,  # Error si no tiene SKU o bodega
            }
            for (d, s, b, c) in cur.fetchall()
        ]

    # Detectar si hay error de sucursal
    # Error si sucursal es None, vacía, o contiene mensaje de error
    tiene_error_sucursal = not sucursal or (sucursal and sucursal.strip().startswith("ERROR:"))
    
    return jsonify({
        "id": pedido_id,
        "numero_pedido": numero_pedido,
        "fecha": fecha.isoformat() if fecha else None,
        "sucursal": sucursal,
        "tiene_error_sucursal": tiene_error_sucursal,
        "cliente_id": cliente_id,
        "cliente_nombre": cliente_nombre,
        "sucursal_id": sucursal_id,
        "orden_compra": orden_compra,
        "cliente_ruc": cliente_ruc,
        "sucursal_ruc": sucursal_ruc,
        "encargado": encargado,
        "items": items
    })

# ====== VERIFICAR PEDIDO =======
@app.route("/api/pedidos/<int:pedido_id>/verificar", methods=["POST"])
def api_verificar_pedido(pedido_id: int):
    """Verifica y actualiza un pedido con errores"""
    try:
        data = request.get_json()
        sucursal = data.get("sucursal", "").strip()
        sucursal_id_enviado = data.get("sucursal_id")  # ID de sucursal enviado desde el frontend
        items_actualizados = data.get("items", [])
        
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el pedido existe y está en estado con_errores
            cur.execute("""
                SELECT estado FROM pedidos WHERE id = %s;
            """, (pedido_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"exito": False, "error": "Pedido no encontrado"}), 404
            
            estado_actual = row[0]
            if estado_actual != "con_errores":
                return jsonify({"exito": False, "error": "El pedido no está en estado con_errores"}), 400
            
            # Obtener el cliente_id del pedido (necesario para buscar bodegas)
            cur.execute("""
                SELECT cliente_id FROM pedidos WHERE id = %s;
            """, (pedido_id,))
            cliente_id = cur.fetchone()[0]
            
            # Verificar si hay error de sucursal (sucursal actual es null, vacía, o contiene mensaje de error)
            cur.execute("""
                SELECT sucursal FROM pedidos WHERE id = %s;
            """, (pedido_id,))
            sucursal_actual = cur.fetchone()[0]
            tiene_error_sucursal = not sucursal_actual or sucursal_actual.strip() == "" or sucursal_actual.strip().startswith("ERROR:")
            
            # Validar y actualizar sucursal solo si hay error de sucursal
            sucursal_id_actualizado = None
            if tiene_error_sucursal:
                if sucursal_id_enviado:
                    # Si se envió un ID de sucursal, usarlo directamente
                    sucursal_id_enviado = int(sucursal_id_enviado)
                    
                    # Verificar que la sucursal existe y pertenece al cliente
                    cur.execute("""
                        SELECT id, nombre, encargado, direccion, ruc
                        FROM sucursales 
                        WHERE id = %s AND cliente_id = %s AND activo = TRUE;
                    """, (sucursal_id_enviado, cliente_id))
                    
                    sucursal_data = cur.fetchone()
                    if not sucursal_data:
                        return jsonify({"exito": False, "error": f"No se encontró la sucursal con ID {sucursal_id_enviado} para este cliente"}), 400
                    
                    sucursal_id_actualizado, nombre_sucursal, encargado, direccion, ruc = sucursal_data
                    
                    # Actualizar pedido con todos los datos de la sucursal
                    cur.execute("""
                        UPDATE pedidos 
                        SET sucursal = %s, sucursal_id = %s
                        WHERE id = %s;
                    """, (nombre_sucursal, sucursal_id_actualizado, pedido_id))
                    
                    print(f"[OK] Pedido {pedido_id} actualizado con sucursal por ID: {nombre_sucursal} (ID: {sucursal_id_actualizado})")
                    print(f"   Encargado: {encargado}, RUC: {ruc}")
                    
                else:
                    # Método anterior: buscar por nombre (para compatibilidad)
                    if not sucursal:
                        return jsonify({"exito": False, "error": "La sucursal es requerida"}), 400
                    
                    # Buscar la sucursal por nombre en las sucursales del cliente
                    cur.execute("""
                        SELECT id, nombre, encargado, direccion, ruc
                        FROM sucursales 
                        WHERE cliente_id = %s AND activo = TRUE 
                        AND (nombre = %s OR alias = %s)
                        LIMIT 1;
                    """, (cliente_id, sucursal, sucursal))
                    
                    sucursal_data = cur.fetchone()
                    if not sucursal_data:
                        return jsonify({"exito": False, "error": f"No se encontró la sucursal '{sucursal}' para este cliente"}), 400
                    
                    sucursal_id_actualizado, nombre_sucursal, encargado, direccion, ruc = sucursal_data
                    
                    # Actualizar pedido con todos los datos de la sucursal
                    cur.execute("""
                        UPDATE pedidos 
                        SET sucursal = %s, sucursal_id = %s
                        WHERE id = %s;
                    """, (nombre_sucursal, sucursal_id_actualizado, pedido_id))
                    
                    print(f"[OK] Pedido {pedido_id} actualizado con sucursal por nombre: {nombre_sucursal} (ID: {sucursal_id_actualizado})")
                    print(f"   Encargado: {encargado}, RUC: {ruc}")
                
            else:
                # Si no hay error de sucursal, usar la sucursal actual
                sucursal = sucursal_actual
                # Obtener el sucursal_id actual
                cur.execute("""
                    SELECT sucursal_id FROM pedidos WHERE id = %s;
                """, (pedido_id,))
                sucursal_id_actualizado = cur.fetchone()[0]
                
                # Si el sucursal_id es None, pero tenemos un nombre de sucursal válido, buscar el ID
                if not sucursal_id_actualizado and sucursal and not sucursal.startswith("ERROR:"):
                    cur.execute("""
                        SELECT id FROM sucursales 
                        WHERE cliente_id = %s AND activo = TRUE 
                        AND (nombre = %s OR alias = %s)
                        LIMIT 1;
                    """, (cliente_id, sucursal, sucursal))
                    resultado_suc = cur.fetchone()
                    if resultado_suc:
                        sucursal_id_actualizado = resultado_suc[0]
                        # Actualizar el pedido con el sucursal_id correcto
                        cur.execute("""
                            UPDATE pedidos 
                            SET sucursal_id = %s
                            WHERE id = %s;
                        """, (sucursal_id_actualizado, pedido_id))
                        print(f"[OK] Sucursal_id asignado: {sucursal_id_actualizado} para pedido {pedido_id}")
            
            # Actualizar items si se proporcionaron
            if items_actualizados:
                # Usar el sucursal_id actualizado (ya obtenido arriba)
                sucursal_id = sucursal_id_actualizado
                
                # Obtener todos los items del pedido ordenados por ID
                cur.execute("""
                    SELECT id FROM pedido_items 
                    WHERE pedido_id = %s 
                    ORDER BY id;
                """, (pedido_id,))
                item_ids = [row[0] for row in cur.fetchall()]
                
                for item in items_actualizados:
                    index = item.get("index")
                    sku = item.get("sku", "").strip()
                    cantidad = item.get("cantidad", 0)
                    
                    if not sku:
                        return jsonify({"exito": False, "error": f"SKU requerido para el producto {index + 1}"}), 400
                    
                    if cantidad <= 0:
                        return jsonify({"exito": False, "error": f"Cantidad debe ser mayor a 0 para el producto {index + 1}"}), 400
                    
                    # Verificar que el índice es válido
                    if index >= len(item_ids):
                        return jsonify({"exito": False, "error": f"Índice de producto inválido: {index}"}), 400
                    
                    # Verificar que el producto existe en la base de datos
                    cur.execute("""
                        SELECT id, nombre FROM productos WHERE sku = %s;
                    """, (sku,))
                    producto = cur.fetchone()
                    if not producto:
                        return jsonify({"exito": False, "error": f"El SKU '{sku}' no existe en el catálogo de productos. Por favor, créalo primero."}), 400
                    
                    producto_id = producto[0]
                    
                    # Actualizar el item específico por ID
                    item_id = item_ids[index]
                    
                    # Buscar bodega automáticamente para el SKU
                    bodega_asignada = None
                    
                    # Primero intentar por sucursal (si el cliente usa bodega por sucursal)
                    if sucursal_id:
                        cur.execute("""
                            SELECT bodega 
                            FROM bodegas_producto_por_sucursal
                            WHERE sucursal_id = %s AND producto_id = %s;
                        """, (sucursal_id, producto_id))
                        resultado = cur.fetchone()
                        if resultado:
                            bodega_asignada = resultado[0]
                    
                    # Si no se encontró por sucursal, intentar por cliente
                    if not bodega_asignada and cliente_id:
                        cur.execute("""
                            SELECT bodega 
                            FROM bodegas_producto_por_cliente
                            WHERE cliente_id = %s AND producto_id = %s;
                        """, (cliente_id, producto_id))
                        resultado = cur.fetchone()
                        if resultado:
                            bodega_asignada = resultado[0]
                    
                    # Actualizar el item con SKU, cantidad y bodega
                    cur.execute("""
                        UPDATE pedido_items 
                        SET sku = %s, cantidad = %s, bodega = %s
                        WHERE id = %s;
                    """, (sku, cantidad, bodega_asignada, item_id))
            
            # Verificar si aún hay errores después de la actualización
            cur.execute("""
                SELECT COUNT(*) FROM pedido_items 
                WHERE pedido_id = %s AND (sku IS NULL OR sku = '' OR bodega IS NULL OR bodega = '');
            """, (pedido_id,))
            items_con_errores = cur.fetchone()[0]
            
            # Verificar si hay error de sucursal después de la actualización
            cur.execute("""
                SELECT sucursal FROM pedidos WHERE id = %s;
            """, (pedido_id,))
            sucursal_actualizada = cur.fetchone()[0]
            tiene_error_sucursal_actualizado = not sucursal_actualizada or sucursal_actualizada.strip() == "" or sucursal_actualizada.strip().startswith("ERROR:")
            
            # Determinar nuevo estado: solo "por_procesar" si no hay errores en items NI en sucursal
            nuevo_estado = "por_procesar" if (items_con_errores == 0 and not tiene_error_sucursal_actualizado) else "con_errores"
            
            # Actualizar estado del pedido
            cur.execute("""
                UPDATE pedidos 
                SET estado = %s 
                WHERE id = %s;
            """, (nuevo_estado, pedido_id))
            
            conn.commit()
            
            return jsonify({
                "exito": True,
                "nuevo_estado": nuevo_estado,
                "mensaje": f"Pedido actualizado. Estado: {nuevo_estado}"
            })
            
    except Exception as e:
        import traceback
        print(f"Error al verificar pedido {pedido_id}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"exito": False, "error": f"Error interno del servidor: {str(e)}"}), 500
    
# Endpoint para subir mapeos de productos (CSV/XLSX)
@app.route("/api/subir_productos", methods=["POST"])
def api_subir_productos():
    """
    Recibe multipart/form-data:
      - archivo: CSV o XLSX con columnas SKU, nombre, bodega
      - cliente_id: int (obligatorio)
      - sucursal_id: int (opcional, solo si el cliente usa bodega por sucursal)
    """
    f = request.files.get("archivo")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No se adjuntó archivo."}), 400

    try:
        cliente_id = int(request.form.get("cliente_id") or "0")
    except ValueError:
        cliente_id = 0
    sucursal_id = request.form.get("sucursal_id")
    try:
        sucursal_id = int(sucursal_id) if sucursal_id not in (None, "", "null", "undefined") else None
    except ValueError:
        sucursal_id = None

    if not cliente_id:
        return jsonify({"ok": False, "error": "cliente_id inválido."}), 400

    # Ejecutar en módulo separado
    try:
        resultado = subir.cargar_y_aplicar_mapeos_productos(
            archivo_bytes=f.read(),
            nombre_archivo=f.filename,
            cliente_id=cliente_id,
            sucursal_id=sucursal_id
        )
        return jsonify({"ok": True, **resultado})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/subir_sucursales", methods=["POST"])
def api_subir_sucursales():
    """
    Recibe multipart/form-data:
      - archivo: CSV o XLSX con columnas SAP, Alias, Encargado, Direccion, Telefono, RUC
      - cliente_id: int (obligatorio)
    """
    f = request.files.get("archivo")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "No se adjuntó archivo."}), 400

    try:
        cliente_id = int(request.form.get("cliente_id") or "0")
    except ValueError:
        cliente_id = 0

    if not cliente_id:
        return jsonify({"ok": False, "error": "cliente_id inválido."}), 400

    # Ejecutar en módulo separado
    try:
        resultado = subir.cargar_y_aplicar_mapeos_sucursales(
            archivo_bytes=f.read(),
            nombre_archivo=f.filename,
            cliente_id=cliente_id
        )
        return jsonify({"ok": True, **resultado})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ========= ENDPOINTS DE CONFIGURACIÓN =========

@app.route("/api/configuracion/numero-pedido-inicial", methods=["GET"])
def api_obtener_numero_pedido_inicial():
    """Obtiene el número de pedido inicial configurado"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT valor FROM configuracion 
                WHERE clave = 'numero_pedido_inicial'
            """)
            result = cur.fetchone()
            
            if result:
                return jsonify({"numero_inicial": int(result[0])})
            else:
                return jsonify({"numero_inicial": 1})  # Valor por defecto
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/configuracion/numero-pedido-inicial", methods=["POST"])
def api_guardar_numero_pedido_inicial():
    """Guarda el número de pedido inicial"""
    try:
        data = request.get_json()
        numero_inicial = data.get("numero_inicial")
        
        if not numero_inicial or not isinstance(numero_inicial, int) or numero_inicial < 1:
            return jsonify({"error": "Número inicial debe ser un entero mayor a 0"}), 400
        
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO configuracion (clave, valor, descripcion) 
                VALUES ('numero_pedido_inicial', %s, 'Número inicial para generar números de pedido secuenciales')
                ON CONFLICT (clave) 
                DO UPDATE SET 
                    valor = EXCLUDED.valor,
                    fecha_actualizacion = CURRENT_TIMESTAMP
            """, (str(numero_inicial),))
            
            conn.commit()
            
        return jsonify({"ok": True, "numero_inicial": numero_inicial})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/configuracion/siguiente-numero-pedido", methods=["GET"])
def api_siguiente_numero_pedido():
    """Obtiene el siguiente número de pedido disponible"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Obtener número inicial configurado
            cur.execute("""
                SELECT valor FROM configuracion 
                WHERE clave = 'numero_pedido_inicial'
            """)
            result = cur.fetchone()
            numero_inicial = int(result[0]) if result else 1
            
            # Obtener el último número de pedido usado
            cur.execute("""
                SELECT COALESCE(MAX(numero_pedido), 0) FROM pedidos
            """)
            ultimo_numero = cur.fetchone()[0]
            
            # Calcular siguiente número
            siguiente_numero = max(numero_inicial, ultimo_numero + 1)
            
            return jsonify({"siguiente_numero": siguiente_numero})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sucursales/cliente/<int:cliente_id>")
def api_sucursales_cliente(cliente_id: int):
    """Obtiene las sucursales activas de un cliente específico"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT s.id, s.nombre, s.alias, s.encargado, s.direccion, s.ruc, s.ciudad
                FROM sucursales s
                WHERE s.cliente_id = %s AND s.activo = TRUE
                ORDER BY upper(s.nombre);
            """, (cliente_id,))
            
            sucursales = []
            for row in cur.fetchall():
                sucursales.append({
                    "id": row[0],
                    "nombre": row[1],
                    "alias": row[2],
                    "encargado": row[3],
                    "direccion": row[4],
                    "ruc": row[5],
                    "ciudad": row[6]
                })
            
            return jsonify({"sucursales": sucursales})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= ENDPOINTS DE GESTIÓN DE ALIAS DE PRODUCTOS =========

@app.route("/api/productos/<int:producto_id>/alias", methods=["GET"])
@login_required
def api_listar_alias_producto(producto_id: int):
    """Lista todos los alias de un producto para un cliente específico"""
    try:
        cliente_id = request.args.get('cliente_id', type=int)
        if not cliente_id:
            return jsonify({"error": "cliente_id es requerido"}), 400
        
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, alias, fecha_creacion, fecha_actualizacion
                FROM producto_alias
                WHERE producto_id = %s AND cliente_id = %s
                ORDER BY fecha_creacion ASC;
            """, (producto_id, cliente_id))
            
            alias = []
            for row in cur.fetchall():
                alias.append({
                    "id": row[0],
                    "alias": row[1],
                    "fecha_creacion": row[2].isoformat() if row[2] else None,
                    "fecha_actualizacion": row[3].isoformat() if row[3] else None
                })
            
            return jsonify({"alias": alias})
            
    except Exception as e:
        print(f"Error al listar alias: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/productos/<int:producto_id>/alias", methods=["POST"])
@login_required
def api_agregar_alias_producto(producto_id: int):
    """Agrega un nuevo alias a un producto"""
    try:
        data = request.get_json()
        cliente_id = data.get("cliente_id")
        alias = data.get("alias", "").strip()
        
        if not cliente_id:
            return jsonify({"error": "cliente_id es requerido"}), 400
        if not alias:
            return jsonify({"error": "El alias no puede estar vacío"}), 400
        
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el producto existe
            cur.execute("SELECT id FROM productos WHERE id = %s", (producto_id,))
            if not cur.fetchone():
                return jsonify({"error": "Producto no encontrado"}), 404
            
            # Verificar que el cliente existe
            cur.execute("SELECT id FROM clientes WHERE id = %s", (cliente_id,))
            if not cur.fetchone():
                return jsonify({"error": "Cliente no encontrado"}), 404
            
            # Insertar el alias
            try:
                cur.execute("""
                    INSERT INTO producto_alias (producto_id, cliente_id, alias)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (producto_id, cliente_id, alias))
                alias_id = cur.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    "ok": True,
                    "alias_id": alias_id,
                    "mensaje": "Alias agregado correctamente"
                })
            except Exception as e:
                # Manejar error de constraint único (alias duplicado)
                if "unique" in str(e).lower():
                    return jsonify({"error": "Este alias ya existe para este producto y cliente"}), 400
                raise
            
    except Exception as e:
        print(f"Error al agregar alias: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/productos/<int:producto_id>/alias/<int:alias_id>", methods=["PUT"])
@login_required
def api_actualizar_alias_producto(producto_id: int, alias_id: int):
    """Actualiza un alias existente"""
    try:
        data = request.get_json()
        alias = data.get("alias", "").strip()
        
        if not alias:
            return jsonify({"error": "El alias no puede estar vacío"}), 400
        
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el alias existe y pertenece al producto
            cur.execute("""
                SELECT id FROM producto_alias
                WHERE id = %s AND producto_id = %s;
            """, (alias_id, producto_id))
            
            if not cur.fetchone():
                return jsonify({"error": "Alias no encontrado"}), 404
            
            # Actualizar el alias
            try:
                cur.execute("""
                    UPDATE producto_alias
                    SET alias = %s, fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (alias, alias_id))
                conn.commit()
                
                return jsonify({
                    "ok": True,
                    "mensaje": "Alias actualizado correctamente"
                })
            except Exception as e:
                # Manejar error de constraint único (alias duplicado)
                if "unique" in str(e).lower():
                    return jsonify({"error": "Este alias ya existe para este producto y cliente"}), 400
                raise
            
    except Exception as e:
        print(f"Error al actualizar alias: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/productos/<int:producto_id>/alias/<int:alias_id>", methods=["DELETE"])
@login_required
def api_eliminar_alias_producto(producto_id: int, alias_id: int):
    """Elimina un alias"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el alias existe y pertenece al producto
            cur.execute("""
                SELECT id FROM producto_alias
                WHERE id = %s AND producto_id = %s;
            """, (alias_id, producto_id))
            
            if not cur.fetchone():
                return jsonify({"error": "Alias no encontrado"}), 404
            
            # Eliminar el alias
            cur.execute("DELETE FROM producto_alias WHERE id = %s;", (alias_id,))
            conn.commit()
            
            return jsonify({
                "ok": True,
                "mensaje": "Alias eliminado correctamente"
            })
            
    except Exception as e:
        print(f"Error al eliminar alias: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clientes/<int:cliente_id>/productos", methods=["GET"])
@login_required
def api_productos_cliente(cliente_id: int):
    """Obtiene todos los productos asociados a un cliente específico"""
    try:
        with db.obtener_conexion() as conn, conn.cursor() as cur:
            # Verificar que el cliente existe
            cur.execute("SELECT id FROM clientes WHERE id = %s", (cliente_id,))
            if not cur.fetchone():
                return jsonify({"error": "Cliente no encontrado"}), 404
            
            # Obtener productos del cliente
            cur.execute("""
                SELECT DISTINCT p.id, p.sku, p.nombre
                FROM productos p
                INNER JOIN bodegas_producto_por_cliente bpc ON p.id = bpc.producto_id
                WHERE bpc.cliente_id = %s
                ORDER BY p.nombre;
            """, (cliente_id,))
            
            productos = []
            for row in cur.fetchall():
                productos.append({
                    "id": row[0],
                    "sku": row[1] or "",
                    "nombre": row[2] or ""
                })
            
            return jsonify({"productos": productos})
            
    except Exception as e:
        print(f"Error al obtener productos del cliente: {e}")
        return jsonify({"error": str(e)}), 500


# ========= ARRANQUE =========

if __name__ == "__main__":
    es_proceso_principal = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)
    if es_proceso_principal:
        print("🚀 Iniciando escucha de correos desde aplicación Flask...")
        hilo_imap = Thread(
            target=escucha_correos.iniciar_escucha_correos,
            args=(al_encontrar_pdf,),
            name="hilo-escucha-imap",
            daemon=True
        )
        hilo_imap.start()
        print("✅ Hilo IMAP iniciado correctamente.")

    app.run(host="0.0.0.0", port=5000, debug=True)