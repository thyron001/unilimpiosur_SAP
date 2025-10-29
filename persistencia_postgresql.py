# persistencia_postgresql.py
# Utilidades para guardar pedidos y sus ítems en PostgreSQL (incluye sucursal y totales).

import os
import psycopg
from datetime import datetime, timezone, timedelta

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv(override=True)  # override=True para que sobrescriba las variables del sistema

# ========================
#  CONEXIÓN
# ========================

def obtener_conexion():
    """
    Crea conexión a PostgreSQL usando variables de entorno PGHOST, PGUSER, etc.
    En local, usa las credenciales del archivo .env
    """
    # Obtener variables de entorno (funcionan tanto en local como en producción)
    # usar os.environ.get en lugar de os.getenv para evitar problemas con variables del sistema
    host = os.environ.get('PGHOST', 'localhost')
    port = os.environ.get('PGPORT', '5432')
    database = os.environ.get('PGDATABASE', 'pedidos')
    user = os.environ.get('PGUSER', 'postgres')
    password = os.environ.get('PGPASSWORD', '')
    
    # Construir connection string para forzar el uso de las variables cargadas
    conninfo = f"host={host} port={port} dbname={database} user={user} password={password}"
    
    return psycopg.connect(conninfo)

# Zona horaria de Ecuador (GMT-5)
ECUADOR_TZ = timezone(timedelta(hours=-5))

def obtener_fecha_local() -> datetime:
    """Obtiene la fecha y hora actual en la zona horaria de Ecuador (GMT-5)"""
    return datetime.now(ECUADOR_TZ)

# ========================
#  CONVERSIÓN
# ========================


# ========================
#  GUARDAR PEDIDO
# ========================

def guardar_pedido(pedido: dict, items: list[dict], cliente_id: int = None, sucursal_id: int = None):
    """
    Inserta en PostgreSQL:

      Tabla pedidos:
        (fecha, sucursal, cliente_id, sucursal_id)

      Tabla pedido_items:
        (pedido_id, descripcion, sku, bodega, cantidad)

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
            fecha = obtener_fecha_local()
    elif not isinstance(fecha, datetime):
        fecha = obtener_fecha_local()


    sucursal = (pedido.get("sucursal") or "").strip() or None
    orden_compra = (pedido.get("orden_compra") or "").strip() or None

    # Detectar errores en productos y sucursal
    tiene_errores = False
    
    # Error si no se detectó sucursal o si contiene mensajes de error
    if not sucursal or sucursal.strip() == "" or "SUCURSAL DESCONOCIDA" in sucursal or sucursal.strip().startswith("ERROR:"):
        tiene_errores = True
    
    # Error si algún producto no tiene SKU o bodega
    if not tiene_errores:
        for item in items:
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
                  (fecha, sucursal, estado, cliente_id, sucursal_id, numero_pedido, orden_compra)
                VALUES
                  (%s,    %s,       %s,     %s,         %s,          %s,           %s)
                RETURNING id;
                """,
                (fecha, sucursal, estado, cliente_id, sucursal_id, siguiente_numero, orden_compra)
            )
            pedido_id = cur.fetchone()[0]
            numero_pedido = siguiente_numero

            # Insert ítems
            for f in items:
                cur.execute(
                    """
                    INSERT INTO pedido_items
                      (pedido_id, descripcion, sku, bodega, cantidad)
                    VALUES
                      (%s,        %s,          %s,  %s,     %s);
                    """,
                    (
                        pedido_id,
                        (f.get("descripcion") or f.get("desc") or "").strip(),
                        f.get("sku"),
                        f.get("bodega"),
                        int(f.get("cantidad") or f.get("cant") or 0),
                    )
                )
    # --- Impresión en terminal con los nuevos valores ---
    print("✅ Pedido guardado en PostgreSQL:")
    print(f"   → ID={pedido_id} | N° orden llegada={numero_pedido} | Ítems={len(items)}")
    print(f"   → Sucursal:        {sucursal or '-'}")

    return pedido_id, numero_pedido, estado
