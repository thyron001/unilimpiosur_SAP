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

def obtener_conexion_pg():
    return psycopg.connect()

def guardar_pedido_en_pg(filas_enriquecidas: list[dict], meta: dict):
    if not filas_enriquecidas:
        print("⚠️ No hay filas enriquecidas para guardar en PostgreSQL.")
        return

    total = Decimal("0")
    for f in filas_enriquecidas:
        pt = a_decimal(f.get("ptotal"))
        if pt is not None:
            total += pt

    fecha = meta.get("fecha")
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except Exception:
            fecha = datetime.now()
    elif not isinstance(fecha, datetime):
        fecha = datetime.now()

    pdf_filename  = meta.get("pdf_filename")
    email_uid     = meta.get("email_uid")
    email_from    = meta.get("email_from")
    email_subject = meta.get("email_subject")

    with obtener_conexion_pg() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pedidos (fecha, total, pdf_filename, email_uid, email_from, email_subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, numero_pedido;
                """,
                (fecha, total, pdf_filename, email_uid, email_from, email_subject)
            )
            pedido_id, numero_pedido = cur.fetchone()

            for f in filas_enriquecidas:
                cur.execute(
                    """
                    INSERT INTO pedido_items
                    (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        pedido_id,
                        (f.get("desc") or "").strip(),
                        f.get("sku"),
                        f.get("bodega"),
                        int(f.get("cant") or 0),
                        a_decimal(f.get("puni")),
                        a_decimal(f.get("ptotal")),
                    )
                )
    print(f"✅ Pedido guardado en PostgreSQL. ID={pedido_id} | N° orden llegada={numero_pedido} | Ítems={len(filas_enriquecidas)}")

# ========= CALLBACK DEL ESCUCHADOR =========

def al_encontrar_pdf(meta: dict, nombre_pdf: str, pdf_en_bytes: bytes) -> None:
    print("\n=== 📬 Nuevo correo (callback) ===")
    print(f"De:      {meta.get('remitente','')}")
    print(f"Asunto:  {meta.get('asunto','')}")
    print(f"Fecha:   {meta.get('fecha')}")
    print(f"UID:     {meta.get('uid')}")
    print(f"📎 PDF:  {nombre_pdf}")

    # 1) Filas de la tabla
    filas = proc.extraer_filas_pdf(pdf_en_bytes)
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return

    # 2) Sucursal y totales (del PDF)
    resumen = proc.extraer_sucursal_y_totales(pdf_en_bytes)

    # 3) Emparejar contra BD (cliente fijo: Roldan), usando el alias de sucursal del PDF
    filas_enriquecidas, suc = proc.emparejar_filas_con_bd(
        filas,
        cliente_nombre="Roldan",
        sucursal_alias=resumen.get("sucursal")
    )

    # 4) Armar dict 'pedido' para persistencia_postgresql.guardar_pedido()
    pedido = {
        "fecha": meta.get("fecha"),
        "sucursal": (suc.get("nombre") if suc else resumen.get("sucursal")),  # nombre del sistema si se encontró
        "subtotal_bruto": resumen.get("subtotal_bruto"),
        "descuento":      resumen.get("descuento"),
        "subtotal_neto":  resumen.get("subtotal_neto"),
        "iva_0":          resumen.get("iva_0"),
        "iva_15":         resumen.get("iva_15"),
        "total":          resumen.get("total"),
    }

    # 5) Guardar en PostgreSQL (usa tu función existente)
    try:
        db.guardar_pedido(pedido, filas_enriquecidas)
    except Exception as e:
        print(f"❌ No se guardó el pedido: {e}")
        return

    # (opcional) logs en terminal
    proc.imprimir_filas_emparejadas(filas_enriquecidas)


# ========= RUTAS FLASK =========

@app.route("/pedidos")
def ver_pedidos():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, numero_pedido, fecha, total, sucursal
            FROM pedidos
            ORDER BY id DESC
            LIMIT 200;
        """)
        filas = [
            {"id": i, "numero_pedido": n, "fecha": f, "total": t, "sucursal": s}
            for (i, n, f, t, s) in cur.fetchall()
        ]
    return render_template("orders.html", orders=filas, now=datetime.utcnow())


@app.route("/clientes")
def vista_clientes():
    return render_template("clientes.html")

@app.route("/api/clientes_con_sucursales")
def api_clientes_con_sucursales():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc, c.usa_bodega_por_sucursal
            FROM clientes c
            ORDER BY upper(c.nombre);
        """)
        clientes = [
            {
                "id": cid, "nombre": nom, "ruc": ruc,
                "usa_bodega_por_sucursal": bool(ubs),
                "sucursales": []
            }
            for (cid, nom, ruc, ubs) in cur.fetchall()
        ]
        idx = {c["id"]: c for c in clientes}

        if clientes:
            cur.execute("""
                SELECT s.id, s.cliente_id, s.alias, s.nombre, s.encargado, s.direccion, s.telefono, s.activo
                FROM sucursales s
                WHERE s.activo = TRUE
                ORDER BY upper(s.nombre);
            """)
            for (sid, cliente_id, alias, nombre, encargado, direccion, telefono, activo) in cur.fetchall():
                if cliente_id in idx:
                    idx[cliente_id]["sucursales"].append({
                        "id": sid, "alias": alias, "nombre": nombre,
                        "encargado": encargado, "direccion": direccion, "telefono": telefono
                    })

    return jsonify(list(idx.values()))


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
            direccion   = (c.get("direccion") or "").strip() or None
            telefono    = (c.get("telefono") or "").strip() or None
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
                       SET nombre = %s, alias = %s, direccion = %s, telefono = %s
                     WHERE id = %s;
                """, (nombre, alias, direccion, telefono, sucursal_id))
                resultados["actualizados"] += (cur.rowcount or 0)
            else:
                cur.execute("""
                    INSERT INTO sucursales (cliente_id, nombre, alias, direccion, telefono, activo)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    RETURNING id;
                """, (cliente_id, nombre, alias, direccion, telefono))
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
            SELECT c.id, c.nombre, c.ruc
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = FALSE
            ORDER BY upper(c.nombre);
        """)
        clientes_pc = [{"id": i, "nombre": n, "ruc": r} for (i,n,r) in cur.fetchall()]
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
                por_cliente.setdefault(cliente_id, []).append({
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                })
        for cid, cli in idmap.items():
            result["por_cliente"].append({
                "cliente": cli,
                "filas": por_cliente.get(cid, [])
            })


        # ------- POR SUCURSAL + CLIENTE -------
        cur.execute("""
            SELECT c.id, c.nombre, c.ruc
            FROM clientes c
            WHERE c.usa_bodega_por_sucursal = TRUE
            ORDER BY upper(c.nombre);
        """)
        clientes_ps = [{"id": i, "nombre": n, "ruc": r} for (i,n,r) in cur.fetchall()]

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
                por_cliente[cli_id][suc_id]["filas"].append({
                    "mapeo_id": mapeo_id,
                    "producto_id": pid,
                    "sku": sku, "nombre_producto": pnom,
                    "bodega": bodega
                })

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

    return jsonify({"ok": True, **res})






@app.route("/api/orders/summary")
def resumen_pedidos():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos;")
        (cantidad,) = cur.fetchone()
    return jsonify({"count": int(cantidad)})


# ====== DETALLE PEDIDO =======
@app.route("/api/pedidos/<int:pedido_id>")
def api_detalle_pedido(pedido_id: int):
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT numero_pedido, fecha, sucursal,
                   subtotal_bruto, descuento, subtotal_neto,
                   iva_0, iva_15, total
            FROM pedidos
            WHERE id = %s;
        """, (pedido_id,))
        row = cur.fetchone()
        if not row:
            return abort(404)

        (numero_pedido, fecha, sucursal,
         subtotal_bruto, descuento, subtotal_neto,
         iva_0, iva_15, total) = row

        cur.execute("""
            SELECT descripcion, sku, bodega, cantidad, precio_unitario, precio_total
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
                "precio_unitario": float(pu) if pu is not None else None,
                "precio_total":   float(pt) if pt is not None else None,
            }
            for (d, s, b, c, pu, pt) in cur.fetchall()
        ]

    return jsonify({
        "id": pedido_id,
        "numero_pedido": numero_pedido,
        "fecha": fecha.isoformat() if fecha else None,
        "sucursal": sucursal,
        "totales": {
            "subtotal_bruto": float(subtotal_bruto) if subtotal_bruto is not None else None,
            "descuento":      float(descuento) if descuento is not None else None,
            "subtotal_neto":  float(subtotal_neto) if subtotal_neto is not None else None,
            "iva_0":          float(iva_0) if iva_0 is not None else None,
            "iva_15":         float(iva_15) if iva_15 is not None else None,
            "total":          float(total) if total is not None else None,
        },
        "items": items
    })
    
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
