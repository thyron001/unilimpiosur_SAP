# persistencia_postgresql.py
# Utilidades para guardar pedidos y sus ítems en PostgreSQL (incluye sucursal y totales).

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
    s = str(valor).strip().replace(",", ".")
    if s == "" or s == "-":
        return None
    try:
        return Decimal(s)
    except Exception:
        return None

# ========================
#  GUARDAR PEDIDO
# ========================

def guardar_pedido(pedido: dict, items: list[dict]):
    """
    Inserta en PostgreSQL:

      Tabla pedidos:
        (fecha, sucursal, subtotal_bruto, descuento, subtotal_neto, iva_0, iva_15, total)

      Tabla pedido_items:
        (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)

    pedido: dict con claves:
      fecha (datetime), sucursal (str),
      subtotal_bruto, descuento, subtotal_neto, iva_0, iva_15, total (Decimal/str)
    """
    # Normalizar fecha
    fecha = pedido.get("fecha")
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except Exception:
            fecha = datetime.now()
    elif not isinstance(fecha, datetime):
        fecha = datetime.now()

    # Totales
    subtotal_bruto = a_decimal(pedido.get("subtotal_bruto"))
    descuento      = a_decimal(pedido.get("descuento"))
    subtotal_neto  = a_decimal(pedido.get("subtotal_neto"))
    iva_0          = a_decimal(pedido.get("iva_0"))
    iva_15         = a_decimal(pedido.get("iva_15"))
    total          = a_decimal(pedido.get("total"))

    # ⚠️ Política: NO calcular el total si no viene del PDF.
    if total is None:
        raise ValueError("TOTAL no detectado en el PDF; se aborta el guardado para evitar cálculos automáticos.")

    sucursal = (pedido.get("sucursal") or "").strip() or None

    with obtener_conexion() as conn:
        with conn.cursor() as cur:
            # Insert pedido con nuevas columnas
            cur.execute(
                """
                INSERT INTO pedidos
                  (fecha, sucursal, subtotal_bruto, descuento, subtotal_neto, iva_0, iva_15, total)
                VALUES
                  (%s,    %s,       %s,             %s,        %s,            %s,   %s,    %s)
                RETURNING id, numero_pedido;
                """,
                (fecha, sucursal, subtotal_bruto, descuento, subtotal_neto, iva_0, iva_15, total)
            )
            pedido_id, numero_pedido = cur.fetchone()

            # Insert ítems
            for f in items:
                cur.execute(
                    """
                    INSERT INTO pedido_items
                      (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)
                    VALUES
                      (%s,        %s,          %s,  %s,     %s,       %s,              %s);
                    """,
                    (
                        pedido_id,
                        (f.get("descripcion") or f.get("desc") or "").strip(),
                        f.get("sku"),
                        f.get("bodega"),
                        int(f.get("cantidad") or f.get("cant") or 0),
                        a_decimal(f.get("precio_unitario") or f.get("puni")),
                        a_decimal(f.get("precio_total") or f.get("ptotal")),
                    )
                )
    # --- Impresión en terminal con los nuevos valores ---
    print("✅ Pedido guardado en PostgreSQL:")
    print(f"   → ID={pedido_id} | N° orden llegada={numero_pedido} | Ítems={len(items)}")
    print(f"   → Sucursal:        {sucursal or '-'}")
    print(f"   → Subtotal bruto:  {subtotal_bruto if subtotal_bruto is not None else '-'}")
    print(f"   → Descuento:       {descuento if descuento is not None else '-'}")
    print(f"   → Subtotal neto:   {subtotal_neto if subtotal_neto is not None else '-'}")
    print(f"   → IVA 0%:          {iva_0 if iva_0 is not None else '-'}")
    print(f"   → IVA 15%:         {iva_15 if iva_15 is not None else '-'}")
    print(f"   → TOTAL:           {total if total is not None else '-'}")

    return pedido_id, numero_pedido
