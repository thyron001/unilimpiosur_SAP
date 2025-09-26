# persistencia_postgresql.py
# Utilidades para guardar pedidos y sus ítems en PostgreSQL (incluye sucursal y totales).

import psycopg
from datetime import datetime

# ========================
#  CONEXIÓN
# ========================

def obtener_conexion():
    """Crea conexión a PostgreSQL usando variables de entorno PGHOST, PGUSER, etc."""
    return psycopg.connect()

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
            fecha = datetime.now()
    elif not isinstance(fecha, datetime):
        fecha = datetime.now()


    sucursal = (pedido.get("sucursal") or "").strip() or None
    comentario = (pedido.get("comentario") or "").strip() or None

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
                  (fecha, sucursal, estado, cliente_id, sucursal_id, numero_pedido, comentario)
                VALUES
                  (%s,    %s,       %s,     %s,         %s,          %s,           %s)
                RETURNING id;
                """,
                (fecha, sucursal, estado, cliente_id, sucursal_id, siguiente_numero, comentario)
            )
            pedido_id = cur.fetchone()[0]
            numero_pedido = siguiente_numero
            
            # Actualizar comentario con el número de pedido real y el encargado de la sucursal
            if comentario and "[NUMERO_PEDIDO]" in comentario:
                comentario_actualizado = comentario.replace("[NUMERO_PEDIDO]", str(numero_pedido))
                
                # Si hay sucursal_id, obtener el encargado de la sucursal
                if sucursal_id and "[ENCARGADO_SUCURSAL]" in comentario_actualizado:
                    cur.execute(
                        """
                        SELECT encargado FROM sucursales WHERE id = %s
                        """,
                        (sucursal_id,)
                    )
                    encargado_result = cur.fetchone()
                    encargado = encargado_result[0] if encargado_result and encargado_result[0] else "Sin encargado"
                    comentario_actualizado = comentario_actualizado.replace("[ENCARGADO_SUCURSAL]", encargado)
                elif "[ENCARGADO_SUCURSAL]" in comentario_actualizado:
                    # Si no hay sucursal_id, usar "Sin sucursal"
                    comentario_actualizado = comentario_actualizado.replace("[ENCARGADO_SUCURSAL]", "Sin sucursal")
                
                cur.execute(
                    """
                    UPDATE pedidos 
                    SET comentario = %s 
                    WHERE id = %s
                    """,
                    (comentario_actualizado, pedido_id)
                )

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
