# main.py — limpio, usando procesamiento_pedidos.py

import os
from datetime import datetime
from decimal import Decimal

import psycopg
from threading import Thread
from flask import Flask, render_template, jsonify, abort
from flask import request

import subir_datos as subir
import escucha_correos                  # escucha IMAP (módulo en español)
import procesamiento_pedidos as proc    # parseo + emparejado
import persistencia_postgresql as db


app = Flask(__name__)

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



# ========= CALLBACK DEL ESCUCHADOR =========

def al_encontrar_pdf(meta: dict, nombre_pdf: str, pdf_en_bytes: bytes) -> None:
    print("\n=== 📬 Nuevo correo (callback) ===")
    print(f"De:      {meta.get('remitente','')}")
    print(f"Asunto:  {meta.get('asunto','')}")
    print(f"Fecha:   {meta.get('fecha')}")
    print(f"UID:     {meta.get('uid')}")
    print(f"📎 PDF:  {nombre_pdf}")

    # VERIFICAR SI YA EXISTE UN PEDIDO CON ESTE UID DE CORREO
    uid_correo = meta.get("uid")
    if uid_correo:
        with db.obtener_conexion() as conn:
            with conn.cursor() as cur:
                # Buscar pedidos recientes con el mismo remitente y asunto (últimas 24 horas)
                cur.execute("""
                    SELECT id FROM pedidos 
                    WHERE fecha >= NOW() - INTERVAL '24 hours'
                    AND sucursal IS NOT NULL
                    ORDER BY id DESC
                    LIMIT 10
                """)
                pedidos_recientes = cur.fetchall()
                
                if pedidos_recientes:
                    print(f"⚠️  Detectado posible duplicado para UID {uid_correo}. Verificando...")
                    # Si hay pedidos muy recientes (últimos 5 minutos), saltar procesamiento
                    cur.execute("""
                        SELECT COUNT(*) FROM pedidos 
                        WHERE fecha >= NOW() - INTERVAL '5 minutes'
                    """)
                    pedidos_muy_recientes = cur.fetchone()[0]
                    if pedidos_muy_recientes > 0:
                        print(f"🚫 Saltando procesamiento: hay {pedidos_muy_recientes} pedido(s) procesado(s) en los últimos 5 minutos")
                        return

    # 1) Filas de la tabla
    filas = proc.extraer_filas_pdf(pdf_en_bytes)
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return

    # 2) Sucursal (del PDF)
    resumen = proc.extraer_sucursal(pdf_en_bytes)

    # 3) Emparejar contra BD (cliente fijo: Roldan), usando el alias de sucursal del PDF
    filas_enriquecidas, suc, cliente_id = proc.emparejar_filas_con_bd(
        filas,
        cliente_nombre="Roldan",
        sucursal_alias=resumen.get("sucursal")
    )

    # 4) Verificar si se encontró la sucursal por alias
    sucursal_alias_pdf = resumen.get("sucursal")
    if sucursal_alias_pdf and not suc:
        # No se encontró coincidencia en el alias - marcar como error
        print(f"❌ ERROR: No se encontró sucursal con alias '{sucursal_alias_pdf}' en la base de datos")
        pedido = {
            "fecha": meta.get("fecha"),
            "sucursal": f"ERROR: Alias '{sucursal_alias_pdf}' no encontrado",
        }
        try:
            pedido_id, numero_pedido, estado = db.guardar_pedido(pedido, filas_enriquecidas, cliente_id, None)
            print(f"⚠️  Pedido guardado con ERROR: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
        except Exception as e:
            print(f"❌ No se guardó el pedido con error: {e}")
        return

    # 5) Armar dict 'pedido' para persistencia_postgresql.guardar_pedido()
    pedido = {
        "fecha": meta.get("fecha"),
        "sucursal": suc.get("nombre") if suc else "SUCURSAL DESCONOCIDA",  # nombre del sistema si se encontró
    }

    # 6) Guardar en PostgreSQL (usa tu función existente)
    try:
        sucursal_id = suc.get("id") if suc else None
        pedido_id, numero_pedido, estado = db.guardar_pedido(pedido, filas_enriquecidas, cliente_id, sucursal_id)
        print(f"✅ Pedido guardado: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
    except Exception as e:
        print(f"❌ No se guardó el pedido: {e}")
        return

    # (opcional) logs en terminal
    proc.imprimir_filas_emparejadas(filas_enriquecidas)



# ========= RUTAS FLASK =========

@app.route("/")
def index():
    """Redirige a la página de pedidos"""
    from flask import redirect, url_for
    return redirect(url_for('ver_pedidos'))

@app.route("/pedidos")
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
def vista_clientes():
    return render_template("clientes.html")

@app.route("/api/clientes")
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
def api_clientes_con_sucursales():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.usa_bodega_por_sucursal, 
                   c.alias_por_sucursal, c.alias_por_producto, c.cantidad_alias_producto,
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
                "cantidad_alias_producto": cantidad_alias or 1,
                "ruc_por_sucursal": bool(ruc_por_suc),
                "sucursales": []
            }
            for (cid, nom, ruc, ubs, alias_suc, alias_prod, cantidad_alias, ruc_por_suc) in cur.fetchall()
        ]
        idx = {c["id"]: c for c in clientes}

        if clientes:
            cur.execute("""
                SELECT s.id, s.cliente_id, s.alias, s.nombre, s.encargado, s.direccion, s.telefono, s.activo, s.ruc, s.bodega
                FROM sucursales s
                WHERE s.activo = TRUE
                ORDER BY upper(s.nombre);
            """)
            for (sid, cliente_id, alias, nombre, encargado, direccion, telefono, activo, ruc, bodega) in cur.fetchall():
                if cliente_id in idx:
                    idx[cliente_id]["sucursales"].append({
                        "id": sid, "alias": alias, "nombre": nombre,
                        "encargado": encargado, "direccion": direccion, "telefono": telefono, "ruc": ruc, "bodega": bodega
                    })

    return jsonify(list(idx.values()))


@app.route("/api/clientes/<int:cliente_id>", methods=["PUT"])
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
                    cantidad_alias_producto = %s,
                    ruc_por_sucursal = %s
                WHERE id = %s
            """, (
                nombre,
                ruc,
                data.get("usa_bodega_por_sucursal", False),
                data.get("alias_por_sucursal", False),
                data.get("alias_por_producto", False),
                data.get("cantidad_alias_producto", 1),
                data.get("ruc_por_sucursal", False),
                cliente_id
            ))
            
            conn.commit()
            
        return jsonify({"ok": True, "mensaje": "Cliente actualizado correctamente"})
        
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        return jsonify({"ok": False, "error": "Error interno del servidor"}), 500


@app.route("/api/sucursales/bulk", methods=["POST"])
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
            telefono    = (c.get("telefono") or "").strip() or None
            ruc         = (c.get("ruc") or "").strip() or None
            bodega      = (c.get("bodega") or "").strip() or None
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
                       SET nombre = %s, alias = %s, encargado = %s, direccion = %s, telefono = %s, ruc = %s, bodega = %s
                     WHERE id = %s;
                """, (nombre, alias, encargado, direccion, telefono, ruc, bodega, sucursal_id))
                resultados["actualizados"] += (cur.rowcount or 0)
            else:
                cur.execute("""
                    INSERT INTO sucursales (cliente_id, nombre, alias, encargado, direccion, telefono, ruc, bodega, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id;
                """, (cliente_id, nombre, alias, encargado, direccion, telefono, ruc, bodega))
                nuevo_id = cur.fetchone()[0]
                resultados["insertados"] += 1

    return jsonify({"ok": True, **resultados})


# === VISTA HTML ===
@app.route("/productos")
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
            SELECT c.id, c.nombre, c.ruc, c.alias_por_producto, c.cantidad_alias_producto
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = FALSE
            ORDER BY upper(c.nombre);
        """)
        clientes_pc = [{"id": i, "nombre": n, "ruc": r, "alias_por_producto": ap, "cantidad_alias_producto": cap} for (i,n,r,ap,cap) in cur.fetchall()]
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
                # Obtener alias para este producto y cliente
                cur.execute("""
                    SELECT alias_1, alias_2, alias_3 
                    FROM alias_productos 
                    WHERE producto_id = %s AND cliente_id = %s;
                """, (pid, cliente_id))
                alias_data = cur.fetchone()
                
                # Construir objeto con alias
                fila = {
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                }
                
                # Agregar alias si existen
                if alias_data:
                    alias_1, alias_2, alias_3 = alias_data
                    if alias_1: fila["alias_1"] = alias_1
                    if alias_2: fila["alias_2"] = alias_2
                    if alias_3: fila["alias_3"] = alias_3
                
                por_cliente.setdefault(cliente_id, []).append(fila)
        for cid, cli in idmap.items():
            result["por_cliente"].append({
                "cliente": cli,
                "filas": por_cliente.get(cid, [])
            })


        # ------- POR SUCURSAL + CLIENTE -------
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.alias_por_producto, c.cantidad_alias_producto
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = TRUE
            ORDER BY upper(c.nombre);
        """)
        clientes_ps = [{"id": i, "nombre": n, "ruc": r, "alias_por_producto": ap, "cantidad_alias_producto": cap} for (i,n,r,ap,cap) in cur.fetchall()]

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
                
                # Obtener alias para este producto y cliente
                cur.execute("""
                    SELECT alias_1, alias_2, alias_3 
                    FROM alias_productos 
                    WHERE producto_id = %s AND cliente_id = %s;
                """, (pid, cli_id))
                alias_data = cur.fetchone()
                
                # Construir objeto con alias
                fila = {
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                }
                
                # Agregar alias si existen
                if alias_data:
                    alias_1, alias_2, alias_3 = alias_data
                    if alias_1: fila["alias_1"] = alias_1
                    if alias_2: fila["alias_2"] = alias_2
                    if alias_3: fila["alias_3"] = alias_3
                
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
            sku          = (c.get("producto_sku") or "").strip() or None
            nombre_prod  = (c.get("producto_nombre") or "").strip() or None
            bodega       = (c.get("bodega") or "").strip() or None
            borrar       = bool(c.get("borrar"))
            
            # Extraer alias
            alias_1 = (c.get("alias_1") or "").strip() or None
            alias_2 = (c.get("alias_2") or "").strip() or None
            alias_3 = (c.get("alias_3") or "").strip() or None

            if borrar and mapeo_id:
                cur.execute("DELETE FROM bodegas_producto_por_cliente WHERE id = %s;", (mapeo_id,))
                res["borrados"] += 1
                continue

            if not sku and not nombre_prod:
                continue  # necesita al menos algo

            # Asegurar producto
            producto_id = None
            if sku:
                cur.execute("SELECT id FROM productos WHERE sku = %s;", (sku,))
                r = cur.fetchone()
                if r: producto_id = r[0]
            if not producto_id and nombre_prod:
                cur.execute("SELECT id FROM productos WHERE upper(nombre) = upper(%s) LIMIT 1;", (nombre_prod,))
                r = cur.fetchone()
                if r: producto_id = r[0]
            if not producto_id:
                cur.execute("""
                    INSERT INTO productos (sku, nombre, activo) VALUES (%s, %s, TRUE)
                    RETURNING id;
                """, (sku, nombre_prod or sku))
                producto_id = cur.fetchone()[0]
                res["productos_creados"] += 1

            # Upsert bodega por cliente
            if mapeo_id:
                cur.execute("""
                    UPDATE bodegas_producto_por_cliente
                       SET producto_id = %s, bodega = %s
                     WHERE id = %s;
                """, (producto_id, bodega, mapeo_id))
                res["actualizados"] += (cur.rowcount or 0)
            else:
                cur.execute("""
                    INSERT INTO bodegas_producto_por_cliente (cliente_id, producto_id, bodega)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (cliente_id, producto_id, bodega))
                _ = cur.fetchone()[0]
                res["insertados"] += 1

            # Manejar alias de productos
            if producto_id and cliente_id:
                # Upsert alias en la tabla alias_productos
                cur.execute("""
                    INSERT INTO alias_productos (producto_id, cliente_id, alias_1, alias_2, alias_3)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (cliente_id, producto_id) 
                    DO UPDATE SET 
                        alias_1 = EXCLUDED.alias_1,
                        alias_2 = EXCLUDED.alias_2,
                        alias_3 = EXCLUDED.alias_3,
                        fecha_actualizacion = CURRENT_TIMESTAMP;
                """, (producto_id, cliente_id, alias_1, alias_2, alias_3))

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
            sku          = (c.get("producto_sku") or "").strip() or None
            nombre_prod  = (c.get("producto_nombre") or "").strip() or None
            bodega       = (c.get("bodega") or "").strip() or None
            borrar       = bool(c.get("borrar"))
            
            # Extraer alias
            alias_1 = (c.get("alias_1") or "").strip() or None
            alias_2 = (c.get("alias_2") or "").strip() or None
            alias_3 = (c.get("alias_3") or "").strip() or None

            if borrar and mapeo_id:
                cur.execute("DELETE FROM bodegas_producto_por_sucursal WHERE id = %s;", (mapeo_id,))
                res["borrados"] += 1
                continue

            if not sku and not nombre_prod:
                continue

            # Asegurar producto
            producto_id = None
            if sku:
                cur.execute("SELECT id FROM productos WHERE sku = %s;", (sku,))
                r = cur.fetchone()
                if r: producto_id = r[0]
            if not producto_id and nombre_prod:
                cur.execute("SELECT id FROM productos WHERE upper(nombre) = upper(%s) LIMIT 1;", (nombre_prod,))
                r = cur.fetchone()
                if r: producto_id = r[0]
            if not producto_id:
                cur.execute("""
                    INSERT INTO productos (sku, nombre, activo) VALUES (%s, %s, TRUE)
                    RETURNING id;
                """, (sku, nombre_prod or sku))
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

            # Manejar alias de productos (para sucursales, necesitamos el cliente_id)
            if producto_id and sucursal_id:
                # Obtener cliente_id de la sucursal
                cur.execute("SELECT cliente_id FROM sucursales WHERE id = %s;", (sucursal_id,))
                cliente_result = cur.fetchone()
                if cliente_result:
                    cliente_id = cliente_result[0]
                    
                    # Upsert alias en la tabla alias_productos
                    cur.execute("""
                        INSERT INTO alias_productos (producto_id, cliente_id, alias_1, alias_2, alias_3)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (cliente_id, producto_id) 
                        DO UPDATE SET 
                            alias_1 = EXCLUDED.alias_1,
                            alias_2 = EXCLUDED.alias_2,
                            alias_3 = EXCLUDED.alias_3,
                            fecha_actualizacion = CURRENT_TIMESTAMP;
                    """, (producto_id, cliente_id, alias_1, alias_2, alias_3))

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
def api_generar_sap():
    """Genera archivos SAP para pedidos seleccionados o todos los por procesar"""
    try:
        import generador_sap
        
        # Obtener datos del request
        data = request.get_json() or {}
        pedidos_ids = data.get('pedidos_ids', [])
        
        # Si no se especifican pedidos, usar todos los por procesar
        if not pedidos_ids:
            odrf_path, drf1_path = generador_sap.generar_archivos_sap()
        else:
            # Generar archivos solo para los pedidos seleccionados
            odrf_path, drf1_path = generador_sap.generar_archivos_sap_por_ids(pedidos_ids)
        
        if odrf_path and drf1_path:
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


# ====== DETALLE PEDIDO =======
@app.route("/api/pedidos/<int:pedido_id>")
def api_detalle_pedido(pedido_id: int):
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT p.numero_pedido, p.fecha, p.sucursal, p.cliente_id, c.nombre as cliente_nombre
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            WHERE p.id = %s;
        """, (pedido_id,))
        row = cur.fetchone()
        if not row:
            return abort(404)

        (numero_pedido, fecha, sucursal, cliente_id, cliente_nombre) = row

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
        "items": items
    })

# ====== VERIFICAR PEDIDO =======
@app.route("/api/pedidos/<int:pedido_id>/verificar", methods=["POST"])
def api_verificar_pedido(pedido_id: int):
    """Verifica y actualiza un pedido con errores"""
    try:
        data = request.get_json()
        sucursal = data.get("sucursal", "").strip()
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
            
            # Verificar si hay error de sucursal (sucursal actual es null, vacía, o contiene mensaje de error)
            cur.execute("""
                SELECT sucursal FROM pedidos WHERE id = %s;
            """, (pedido_id,))
            sucursal_actual = cur.fetchone()[0]
            tiene_error_sucursal = not sucursal_actual or sucursal_actual.strip() == "" or sucursal_actual.strip().startswith("ERROR:")
            
            # Validar y actualizar sucursal solo si hay error de sucursal
            if tiene_error_sucursal:
                if not sucursal:
                    return jsonify({"exito": False, "error": "La sucursal es requerida"}), 400
                
                # Actualizar sucursal del pedido
                cur.execute("""
                    UPDATE pedidos 
                    SET sucursal = %s 
                    WHERE id = %s;
                """, (sucursal, pedido_id))
            else:
                # Si no hay error de sucursal, usar la sucursal actual
                sucursal = sucursal_actual
            
            # Actualizar items si se proporcionaron
            if items_actualizados:
                # Obtener información del pedido (cliente_id y sucursal_id)
                cur.execute("""
                    SELECT cliente_id, sucursal_id FROM pedidos WHERE id = %s;
                """, (pedido_id,))
                pedido_info = cur.fetchone()
                cliente_id = pedido_info[0] if pedido_info else None
                sucursal_id = pedido_info[1] if pedido_info else None
                
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
                    
                    # Actualizar el item específico por ID
                    item_id = item_ids[index]
                    
                    # Buscar bodega automáticamente para el SKU
                    bodega_asignada = None
                    
                    # Primero intentar por sucursal (si el cliente usa bodega por sucursal)
                    if sucursal_id:
                        cur.execute("""
                            SELECT bps.bodega 
                            FROM bodegas_producto_por_sucursal bps
                            WHERE bps.sucursal_id = %s AND bps.producto_id = (
                                SELECT id FROM productos WHERE sku = %s
                            )
                        """, (sucursal_id, sku))
                        resultado = cur.fetchone()
                        if resultado:
                            bodega_asignada = resultado[0]
                    
                    # Si no se encontró por sucursal, intentar por cliente
                    if not bodega_asignada and cliente_id:
                        cur.execute("""
                            SELECT bpc.bodega 
                            FROM bodegas_producto_por_cliente bpc
                            WHERE bpc.cliente_id = %s AND bpc.producto_id = (
                                SELECT id FROM productos WHERE sku = %s
                            )
                        """, (cliente_id, sku))
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
                SELECT s.id, s.nombre, s.alias, s.encargado, s.direccion, s.telefono
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
                    "telefono": row[5]
                })
            
            return jsonify({"sucursales": sucursales})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========= ARRANQUE =========

if __name__ == "__main__":
    es_proceso_principal = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)
    if es_proceso_principal:
        hilo_imap = Thread(
            target=escucha_correos.iniciar_escucha_correos,
            args=(al_encontrar_pdf,),
            name="hilo-escucha-imap",
            daemon=True
        )
        hilo_imap.start()
        print("🧵 Hilo IMAP iniciado.")

    app.run(host="0.0.0.0", port=5000, debug=True)