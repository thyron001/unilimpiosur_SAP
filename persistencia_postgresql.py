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

def guardar_pedido(pedido: dict, items: list[dict], cliente_id: int = None, sucursal_id: int = None):
    """
    Inserta en PostgreSQL:

      Tabla pedidos:
        (fecha, sucursal, cliente_id, sucursal_id)

      Tabla pedido_items:
        (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)

    pedido: dict con claves:
      fecha (datetime), sucursal (str)
    cliente_id: ID del cliente (opcional)
    sucursal_id: ID de la sucursal (opcional)
    
    Retorna: (pedido_id, numero_pedido, estado)
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


    sucursal = (pedido.get("sucursal") or "").strip() or None

    # Detectar errores en productos
    tiene_errores = False
    for item in items:
        # Un producto tiene error si no tiene SKU o no tiene bodega
        if not item.get("sku") or not item.get("bodega"):
            tiene_errores = True
            break
    
    # Determinar estado del pedido
    estado = "con_errores" if tiene_errores else "por_procesar"

    with obtener_conexion() as conn:
        with conn.cursor() as cur:
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
            
            # Calcular siguiente número de pedido
            siguiente_numero = max(numero_inicial, ultimo_numero + 1)
            
            # Insert pedido con número calculado
            cur.execute(
                """
                INSERT INTO pedidos
                  (fecha, sucursal, estado, cliente_id, sucursal_id, numero_pedido)
                VALUES
                  (%s,    %s,       %s,     %s,         %s,          %s)
                RETURNING id;
                """,
                (fecha, sucursal, estado, cliente_id, sucursal_id, siguiente_numero)
            )
            pedido_id = cur.fetchone()[0]
            numero_pedido = siguiente_numero

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

    return pedido_id, numero_pedido, estado
