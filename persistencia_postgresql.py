# persistencia_postgresql.py
# Utilidades para guardar pedidos y sus ítems en PostgreSQL

import psycopg
from datetime import datetime
from decimal import Decimal

# ========================
#  CONEXIÓN
# ========================

def obtener_conexion():
    """Crea conexión a PostgreSQL usando variables de entorno PGHOST, PGUSER, etc."""
    return psycopg.connect()

# ========================
#  CONVERSIÓN
# ========================

def a_decimal(valor) -> Decimal | None:
    """Convierte strings como '12,50' o '12.50' en Decimal. Devuelve None si no aplica."""
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

# ========================
#  GUARDAR PEDIDO
# ========================

def guardar_pedido(filas_enriquecidas: list[dict], meta: dict):
    """
    Inserta en PostgreSQL:
      - Tabla pedidos(fecha, total, pdf_filename, email_uid, email_from, email_subject)
      - Tabla pedido_items(pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)

    filas_enriquecidas: lista de dicts con desc, cant, puni, ptotal, sku, bodega
    meta: {fecha, pdf_filename, email_uid, email_from, email_subject}
    """
    if not filas_enriquecidas:
        print("⚠️ No hay filas para guardar en PostgreSQL.")
        return

    # Calcular total (si no viene del PDF)
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

    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            # Insert pedido
            cur.execute(
                """
                INSERT INTO pedidos (fecha, total, pdf_filename, email_uid, email_from, email_subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, numero_pedido;
                """,
                (fecha, total, pdf_filename, email_uid, email_from, email_subject)
            )
            pedido_id, numero_pedido = cur.fetchone()

            # Insert ítems
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
