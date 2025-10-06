# generador_sap.py
# Generador de archivos ODRF.txt y DRF1.txt para SAP

import psycopg
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

def obtener_conexion():
    """Crea conexión a PostgreSQL usando variables de entorno PGHOST, PGUSER, etc."""
    return psycopg.connect()

def formatear_fecha_yyyymmdd(fecha: datetime | str | None) -> str:
    """Convierte fecha a formato YYYYMMDD para SAP"""
    if fecha is None:
        fecha = datetime.now()
    elif isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except Exception:
            fecha = datetime.now()
    
    return fecha.strftime("%Y%m%d")

def obtener_pedidos_por_procesar() -> List[Dict[str, Any]]:
    """Obtiene todos los pedidos en estado 'por_procesar' con sus datos completos"""
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
                p.id,
                p.numero_pedido,
                p.fecha,
                p.sucursal,
                p.cliente_id,
                p.sucursal_id,
                c.ruc as cliente_ruc,
                c.ruc_por_sucursal,
                c.nombre as cliente_nombre,
                s.nombre as sucursal_nombre,
                s.direccion,
                s.almacen,
                s.ruc as sucursal_ruc,
                s.ciudad,
                p.orden_compra,
                s.encargado
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN sucursales s ON s.id = p.sucursal_id
            WHERE p.estado = 'por_procesar'
            ORDER BY p.numero_pedido;
        """)
        
        pedidos = []
        for row in cur.fetchall():
            pedidos.append({
                "id": row[0],
                "numero_pedido": row[1],
                "fecha": row[2],
                "sucursal": row[3],
                "cliente_id": row[4],
                "sucursal_id": row[5],
                "cliente_ruc": row[6],
                "ruc_por_sucursal": bool(row[7]),
                "cliente_nombre": row[8],
                "sucursal_nombre": row[9],
                "direccion": row[10],
                "almacen": row[11],
                "sucursal_ruc": row[12],
                "ciudad": row[13],
                "orden_compra": row[14],
                "encargado": row[15]
            })
        
        return pedidos

def obtener_items_pedido(pedido_id: int) -> List[Dict[str, Any]]:
    """Obtiene los items de un pedido específico con información de bodega"""
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                pi.id,
                pi.sku,
                pi.cantidad,
                pi.bodega,
                p.nombre as producto_nombre,
                s.nombre as sucursal_nombre
            FROM pedido_items pi
            LEFT JOIN (
                SELECT DISTINCT sku, nombre 
                FROM productos 
                WHERE sku IS NOT NULL
            ) p ON p.sku = pi.sku
            LEFT JOIN pedidos ped ON ped.id = pi.pedido_id
            LEFT JOIN sucursales s ON s.id = ped.sucursal_id
            WHERE pi.pedido_id = %s
            ORDER BY pi.id;
        """, (pedido_id,))
        
        items = []
        for row in cur.fetchall():
            items.append({
                "sku": row[1],
                "cantidad": row[2],
                "bodega": row[3],
                "producto_nombre": row[4],
                "sucursal_nombre": row[5]
            })
        
        return items

def generar_archivo_odrf(pedidos: List[Dict[str, Any]], ruta_salida: str | Path) -> None:
    """Genera el archivo ODRF.txt con los encabezados y datos de pedidos"""
    ruta_salida = Path(ruta_salida)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        # Escribir ambos encabezados como en ODRF FINAL.txt
        f.write("DocEntry\tDocNum\tDocType\tPrinted\tDocDate\tDocDueDate\tCardCode\tDocObjectCode\tSeries\tShipToCode\tComments\n")
        f.write("DocEntry\tDocNum\tDocType\tPrinted\tDocDate\tDocDueDate\tCardCode\tObjType\tSeries\tShipToCode\tComments\n")
        
        # Escribir datos de cada pedido
        for pedido in pedidos:
            # Formatear RUC como CLXXXXXXXXXXXXX (cliente o sucursal según configuración)
            ruc_fuente = pedido.get("cliente_ruc", "")
            if pedido.get("ruc_por_sucursal"):
                ruc_suc = pedido.get("sucursal_ruc") or ""
                if ruc_suc:
                    ruc_fuente = ruc_suc
            ruc = ruc_fuente
            
            if ruc and not ruc.startswith("CL"):
                # Limpiar RUC de espacios y caracteres especiales
                ruc_limpio = ''.join(filter(str.isdigit, str(ruc)))
                if ruc_limpio:
                    cardcode = f"CL{ruc_limpio.zfill(13)}"
                else:
                    cardcode = "CL0000000000000"
            else:
                cardcode = ruc or "CL0000000000000"
            
            # Fecha en formato YYYYMMDD
            fecha_str = formatear_fecha_yyyymmdd(pedido.get("fecha"))
            
            # Sucursal (ShipToCode) - nombre completo
            ship_to_code = pedido.get("sucursal_nombre") or pedido.get("sucursal") or ""
            
            # Almacén - tomar el almacen (código SAP) directamente de la sucursal
            almacen = pedido.get("almacen") or "5"  # Default almacén 5
            
            # Comments: formato -> Código SAP (nombre completo sucursal) | URBANO | Orden de compra: XXX | Encargado: XXX
            comentarios_partes = []
            
            # 1. Código SAP = Nombre completo de la sucursal (son lo mismo)
            if ship_to_code:
                comentarios_partes.append(ship_to_code)
            
            # 3. "URBANO" si la ciudad NO es Cuenca
            ciudad = (pedido.get("ciudad") or "").strip()
            if ciudad and ciudad.upper() != "CUENCA":
                comentarios_partes.append("URBANO")
            
            # 4. Número de orden de compra con etiqueta
            orden_compra = (pedido.get("orden_compra") or "").strip()
            if orden_compra:
                comentarios_partes.append(f"Orden de compra: {orden_compra}")
            
            # 5. Nombre del encargado con etiqueta
            encargado = (pedido.get("encargado") or "").strip()
            if encargado:
                comentarios_partes.append(f"Encargado: {encargado}")
            
            # Unir todas las partes con pipe separado por espacios
            comments = " | ".join(comentarios_partes)
            
            # Escribir línea (sin UseShpdGd ya que no está en los encabezados)
            f.write(f"{pedido['numero_pedido']}\t")  # DocEntry
            f.write(f"{pedido['numero_pedido']}\t")  # DocNum
            f.write("dDocument_Items\t")             # DocType
            f.write("Y\t")                           # Printed
            f.write(f"{fecha_str}\t")                # DocDate
            f.write(f"{fecha_str}\t")                # DocDueDate
            f.write(f"{cardcode}\t")                 # CardCode
            f.write("17\t")                          # ObjType
            f.write("13\t")                          # Series
            f.write(f"{ship_to_code}\t")             # ShipToCode
            f.write(f"{comments}\n")                 # Comments

def generar_archivo_drf1(pedidos: List[Dict[str, Any]], ruta_salida: str | Path) -> None:
    """Genera el archivo DRF1.txt con los encabezados y datos de items"""
    ruta_salida = Path(ruta_salida)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        # Escribir ambos encabezados como en DRF1 FINAL.txt
        f.write("ParentKey\tItemCode\tPrice\tQuantity\tWarehouseCode\tShipToCode\n")
        f.write("DocNum\tItemCode\tPrice\tQuantity\tWhsCode\tCogsOcrCo5\n")
        
        # Escribir datos de cada item de cada pedido
        for pedido in pedidos:
            items = obtener_items_pedido(pedido["id"])
            
            for item in items:
                # Bodega (WhsCode) - usar la bodega del item o default
                whs_code = item.get("bodega") or "05"  # Default bodega 05
                
                # Sucursal (CogsOcrCo5)
                cogs_ocr_co5 = item.get("sucursal_nombre") or pedido.get("sucursal_nombre") or pedido.get("sucursal") or ""
                
                # Escribir línea (sin UseShpdGd ya que no está en los encabezados)
                f.write(f"{pedido['numero_pedido']}\t")  # DocNum
                f.write(f"{item['sku'] or ''}\t")        # ItemCode
                f.write("1\t")                           # Price (fijo 1)
                f.write(f"{item['cantidad'] or 0}\t")    # Quantity
                f.write(f"{str(whs_code).zfill(2)}\t")   # WhsCode (2 dígitos)
                f.write(f"{cogs_ocr_co5}\n")             # CogsOcrCo5

def actualizar_estado_pedidos(pedido_ids: List[int], nuevo_estado: str) -> None:
    """Actualiza el estado de los pedidos especificados"""
    if not pedido_ids:
        return
    
    with obtener_conexion() as conn, conn.cursor() as cur:
        placeholders = ','.join(['%s'] * len(pedido_ids))
        cur.execute(f"""
            UPDATE pedidos 
            SET estado = %s 
            WHERE id IN ({placeholders})
        """, [nuevo_estado] + pedido_ids)
        
        print(f"OK: Actualizados {cur.rowcount} pedidos a estado '{nuevo_estado}'")

def obtener_pedidos_por_ids(pedidos_ids: List[int]) -> List[Dict[str, Any]]:
    """Obtiene pedidos específicos por sus IDs con sus datos completos, SOLO si están en estado 'por_procesar'"""
    if not pedidos_ids:
        return []
    
    with obtener_conexion() as conn, conn.cursor() as cur:
        placeholders = ','.join(['%s'] * len(pedidos_ids))
        cur.execute(f"""
            SELECT 
                p.id,
                p.numero_pedido,
                p.fecha,
                p.sucursal,
                p.cliente_id,
                p.sucursal_id,
                c.ruc as cliente_ruc,
                c.ruc_por_sucursal,
                c.nombre as cliente_nombre,
                s.nombre as sucursal_nombre,
                s.direccion,
                s.almacen,
                s.ruc as sucursal_ruc,
                s.ciudad,
                p.orden_compra,
                s.encargado
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN sucursales s ON s.id = p.sucursal_id
            WHERE p.id IN ({placeholders}) AND p.estado = 'por_procesar'
            ORDER BY p.numero_pedido;
        """, pedidos_ids)
        
        pedidos = []
        for row in cur.fetchall():
            pedidos.append({
                "id": row[0],
                "numero_pedido": row[1],
                "fecha": row[2],
                "sucursal": row[3],
                "cliente_id": row[4],
                "sucursal_id": row[5],
                "cliente_ruc": row[6],
                "ruc_por_sucursal": bool(row[7]),
                "cliente_nombre": row[8],
                "sucursal_nombre": row[9],
                "direccion": row[10],
                "almacen": row[11],
                "sucursal_ruc": row[12],
                "ciudad": row[13],
                "orden_compra": row[14],
                "encargado": row[15]
            })
        
        return pedidos

def generar_archivos_sap(carpeta_salida: str | Path = None) -> Tuple[str, str]:
    """
    Función principal que genera los archivos ODRF.txt y DRF1.txt
    para todos los pedidos en estado 'por_procesar'
    
    Args:
        carpeta_salida: Si es None, usa archivos temporales. Si se especifica, usa esa carpeta.
    
    Returns:
        Tuple[str, str]: Rutas de los archivos generados (odrf_path, drf1_path)
    """
    import tempfile
    
    # Obtener pedidos por procesar
    pedidos = obtener_pedidos_por_procesar()
    
    if not pedidos:
        print("WARNING: No hay pedidos en estado 'por_procesar' para generar archivos SAP")
        return None, None
    
    print(f"Generando archivos SAP para {len(pedidos)} pedidos...")
    
    # Usar archivos temporales si no se especifica carpeta
    if carpeta_salida is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        odrf_path = Path(tempfile.gettempdir()) / f"ODRF_{timestamp}.txt"
        drf1_path = Path(tempfile.gettempdir()) / f"DRF1_{timestamp}.txt"
    else:
        carpeta_salida = Path(carpeta_salida)
        carpeta_salida.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        odrf_path = carpeta_salida / f"ODRF_{timestamp}.txt"
        drf1_path = carpeta_salida / f"DRF1_{timestamp}.txt"
    
    generar_archivo_odrf(pedidos, odrf_path)
    generar_archivo_drf1(pedidos, drf1_path)
    
    # Actualizar estado de pedidos a 'procesado'
    pedido_ids = [p["id"] for p in pedidos]
    actualizar_estado_pedidos(pedido_ids, "procesado")
    
    print(f"OK: Archivos SAP generados:")
    print(f"   -> ODRF: {odrf_path}")
    print(f"   -> DRF1: {drf1_path}")
    print(f"   -> {len(pedidos)} pedidos marcados como 'procesado'")
    
    return str(odrf_path), str(drf1_path)

def generar_archivos_sap_por_ids(pedidos_ids: List[int], carpeta_salida: str | Path = None) -> Tuple[str, str]:
    """
    Función que genera los archivos ODRF.txt y DRF1.txt
    para pedidos específicos por sus IDs
    
    Args:
        pedidos_ids: Lista de IDs de pedidos a procesar
        carpeta_salida: Si es None, usa archivos temporales. Si se especifica, usa esa carpeta.
    
    Returns:
        Tuple[str, str]: Rutas de los archivos generados (odrf_path, drf1_path)
    """
    import tempfile
    
    # Obtener pedidos específicos
    pedidos = obtener_pedidos_por_ids(pedidos_ids)
    
    if not pedidos:
        print("WARNING: No se encontraron pedidos en estado 'por_procesar' con los IDs especificados")
        # Verificar si hay pedidos con errores en la lista
        with obtener_conexion() as conn, conn.cursor() as cur:
            placeholders = ','.join(['%s'] * len(pedidos_ids))
            cur.execute(f"""
                SELECT id, numero_pedido, estado FROM pedidos 
                WHERE id IN ({placeholders}) AND estado = 'con_errores'
            """, pedidos_ids)
            pedidos_con_errores = cur.fetchall()
            
            if pedidos_con_errores:
                print(f"WARNING: Se encontraron {len(pedidos_con_errores)} pedidos con errores que no se pueden procesar:")
                for pedido_id, numero_pedido, estado in pedidos_con_errores:
                    print(f"   -> Pedido #{numero_pedido} (ID: {pedido_id}) - Estado: {estado}")
                print("   -> Estos pedidos deben ser corregidos antes de poder generar archivos SAP")
        
        return None, None
    
    print(f"Generando archivos SAP para {len(pedidos)} pedidos seleccionados...")
    
    # Usar archivos temporales si no se especifica carpeta
    if carpeta_salida is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        odrf_path = Path(tempfile.gettempdir()) / f"ODRF_{timestamp}.txt"
        drf1_path = Path(tempfile.gettempdir()) / f"DRF1_{timestamp}.txt"
    else:
        carpeta_salida = Path(carpeta_salida)
        carpeta_salida.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        odrf_path = carpeta_salida / f"ODRF_{timestamp}.txt"
        drf1_path = carpeta_salida / f"DRF1_{timestamp}.txt"
    
    generar_archivo_odrf(pedidos, odrf_path)
    generar_archivo_drf1(pedidos, drf1_path)
    
    # Actualizar estado de pedidos a 'procesado' - SOLO los que realmente se procesaron
    pedidos_procesados_ids = [p["id"] for p in pedidos]
    actualizar_estado_pedidos(pedidos_procesados_ids, "procesado")
    
    print(f"OK: Archivos SAP generados:")
    print(f"   -> ODRF: {odrf_path}")
    print(f"   -> DRF1: {drf1_path}")
    print(f"   -> {len(pedidos)} de {len(pedidos_ids)} pedidos procesados (solo los que estaban en estado 'por_procesar')")
    
    return str(odrf_path), str(drf1_path)

if __name__ == "__main__":
    # Ejecutar generación de archivos
    odrf_path, drf1_path = generar_archivos_sap()
    if odrf_path and drf1_path:
        print("SUCCESS: Generación completada exitosamente")
    else:
        print("ERROR: No se generaron archivos")
