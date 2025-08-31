# main.py — limpio, usando procesamiento_pedidos.py

import os
from datetime import datetime
from decimal import Decimal

import psycopg
from threading import Thread
from flask import Flask, render_template, jsonify, abort

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

    filas = proc.extraer_filas_pdf(pdf_en_bytes)
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return

    filas_enriquecidas = proc.emparejar_filas_con_catalogo(filas, proc.RUTA_CATALOGO)
    proc.imprimir_filas_emparejadas(filas_enriquecidas)
    proc.guardar_asignaciones_csv(filas_enriquecidas)

    meta_pedido = {
        "fecha": meta.get("fecha"),
        "pdf_filename": nombre_pdf,
        "email_uid": int(meta.get("uid") or 0),
        "email_from": meta.get("remitente"),
        "email_subject": meta.get("asunto"),
    }
    db.guardar_pedido(filas_enriquecidas, meta_pedido)


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
