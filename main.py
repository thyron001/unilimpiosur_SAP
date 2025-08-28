# main.py — limpio, usando procesamiento_pedidos.py

import os
from datetime import datetime
from decimal import Decimal

import psycopg
from threading import Thread
from flask import Flask, render_template, jsonify

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
            SELECT numero_pedido, fecha, total
            FROM pedidos
            ORDER BY id DESC
            LIMIT 200;
        """)
        filas = [{"numero_pedido": n, "fecha": f, "total": t}
                 for (n, f, t) in cur.fetchall()]
    return render_template("orders.html", orders=filas, now=datetime.utcnow())

@app.route("/api/orders/summary")
def resumen_pedidos():
    with db.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos;")
        (cantidad,) = cur.fetchone()
    return jsonify({"count": int(cantidad)})

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
