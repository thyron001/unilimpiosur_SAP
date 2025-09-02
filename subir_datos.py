# subir_datos.py
# Lógica para subir y aplicar mapeos de productos desde CSV/XLSX.
# Columnas requeridas (case-insensitive): SKU, nombre, bodega

from __future__ import annotations
import io
import csv
from typing import Any, Dict, List, Tuple, Iterable
import persistencia_postgresql as db

# Intentar soportar .xlsx sin obligar a pandas.
try:
    import openpyxl  # para leer .xlsx
except Exception:
    openpyxl = None

def _norm(s: Any) -> str:
    return (str(s).strip() if s is not None else "")

def _leer_csv(buf: bytes) -> List[Dict[str, Any]]:
    filas: List[Dict[str, Any]] = []
    txt = buf.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(txt))
    for raw in reader:
        filas.append({k: raw.get(k) for k in raw.keys()})
    return filas

def _leer_xlsx(buf: bytes) -> List[Dict[str, Any]]:
    if openpyxl is None:
        raise RuntimeError("No se puede leer .xlsx: instala openpyxl o sube un CSV.")
    wb = openpyxl.load_workbook(io.BytesIO(buf), data_only=True)
    ws = wb.active  # primera hoja
    # Encabezados
    headers = []
    for cell in next(ws.iter_rows(min_row=1, max_row=1)):
        headers.append(_norm(cell.value))
    rows: List[Dict[str, Any]] = []
    for row in ws.iter_rows(min_row=2):
        d = {}
        for i, cell in enumerate(row):
            key = headers[i] if i < len(headers) else f"col{i+1}"
            d[key] = cell.value
        rows.append(d)
    return rows

def _estandarizar_columnas(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Acepta headers en cualquier combinación de mayúsculas/minúsculas/espacios:
    SKU / sku / Sku, nombre / Nombre, bodega / BODEGA
    """
    salida: List[Dict[str, Any]] = []
    def keymap(k: str) -> str:
        k2 = (k or "").strip().lower()
        if k2 in ("sku", "código", "codigo", "itemcode", "item"):
            return "sku"
        if k2 in ("nombre", "name", "descripcion", "descripción"):
            return "nombre"
        if k2 in ("bodega", "whscode", "warehouse"):
            return "bodega"
        return k2  # se ignora lo demás
    for r in rows:
        nr = { keymap(k): (r.get(k)) for k in r.keys() }
        # normalizar strings
        nr["sku"]    = _norm(nr.get("sku"))
        nr["nombre"] = _norm(nr.get("nombre"))
        nr["bodega"] = _norm(nr.get("bodega"))
        salida.append(nr)
    return salida

def _asegurar_producto(cur, sku: str, nombre: str) -> int | None:
    """
    Si existe por SKU, devuelve id.
    Si no hay SKU, intenta por nombre (CI).
    Si no existe y NO hay SKU, no puede crear (SKU es NOT NULL) -> retorna None.
    Si no existe y hay SKU, crea el producto con ese SKU y nombre (o usa SKU como nombre si vacío).
    """
    # Primero por SKU
    if sku:
        cur.execute("SELECT id FROM productos WHERE sku = %s;", (sku,))
        r = cur.fetchone()
        if r:
            return int(r[0])
    # Intentar por nombre si no hay SKU
    if not sku and nombre:
        cur.execute("SELECT id FROM productos WHERE upper(nombre) = upper(%s) LIMIT 1;", (nombre,))
        r = cur.fetchone()
        if r:
            return int(r[0])
    # Crear solo si hay SKU
    if sku:
        cur.execute("""
            INSERT INTO productos (sku, nombre, activo)
            VALUES (%s, %s, TRUE)
            RETURNING id;
        """, (sku, nombre or sku))
        return int(cur.fetchone()[0])
    return None

def _upsert_bodega_por_cliente(conn, cliente_id: int, filas: Iterable[Dict[str,str]]) -> Tuple[int,int,int,List[str]]:
    ins = act = om = 0
    errores: List[str] = []
    with conn.cursor() as cur:
        for i, r in enumerate(filas, start=2):  # +2 por encabezado
            sku, nombre, bodega = r.get("sku",""), r.get("nombre",""), r.get("bodega","")
            if not (sku or nombre):
                om += 1; continue
            if not bodega:
                errores.append(f"Fila {i}: bodega vacía.")
                om += 1; continue
            pid = _asegurar_producto(cur, sku, nombre)
            if not pid:
                errores.append(f"Fila {i}: no existe producto y falta SKU para crearlo (nombre='{nombre}').")
                om += 1; continue
            # update si existe, sino insert
            cur.execute("""
                SELECT id FROM bodegas_producto_por_cliente
                WHERE cliente_id = %s AND producto_id = %s;
            """, (cliente_id, pid))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE bodegas_producto_por_cliente
                       SET bodega = %s
                     WHERE id = %s;
                """, (bodega, int(row[0])))
                act += 1
            else:
                cur.execute("""
                    INSERT INTO bodegas_producto_por_cliente (cliente_id, producto_id, bodega)
                    VALUES (%s, %s, %s);
                """, (cliente_id, pid, bodega))
                ins += 1
    return ins, act, om, errores

def _upsert_bodega_por_sucursal(conn, sucursal_id: int, filas: Iterable[Dict[str,str]]) -> Tuple[int,int,int,List[str]]:
    ins = act = om = 0
    errores: List[str] = []
    with conn.cursor() as cur:
        for i, r in enumerate(filas, start=2):
            sku, nombre, bodega = r.get("sku",""), r.get("nombre",""), r.get("bodega","")
            if not (sku or nombre):
                om += 1; continue
            if not bodega:
                errores.append(f"Fila {i}: bodega vacía.")
                om += 1; continue
            pid = _asegurar_producto(cur, sku, nombre)
            if not pid:
                errores.append(f"Fila {i}: no existe producto y falta SKU para crearlo (nombre='{nombre}').")
                om += 1; continue
            # update/insert
            cur.execute("""
                SELECT id FROM bodegas_producto_por_sucursal
                WHERE sucursal_id = %s AND producto_id = %s;
            """, (sucursal_id, pid))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE bodegas_producto_por_sucursal
                       SET bodega = %s
                     WHERE id = %s;
                """, (bodega, int(row[0])))
                act += 1
            else:
                cur.execute("""
                    INSERT INTO bodegas_producto_por_sucursal (sucursal_id, producto_id, bodega)
                    VALUES (%s, %s, %s);
                """, (sucursal_id, pid, bodega))
                ins += 1
    return ins, act, om, errores

def _verificar_modalidad_cliente(cur, cliente_id: int) -> bool:
    cur.execute("SELECT COALESCE(usa_bodega_por_sucursal, FALSE) FROM clientes WHERE id = %s;", (cliente_id,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError("cliente_id no existe.")
    return bool(row[0])

def _validar_sucursal_pertenece(cur, sucursal_id: int, cliente_id: int) -> None:
    cur.execute("SELECT 1 FROM sucursales WHERE id = %s AND cliente_id = %s AND activo = TRUE;", (sucursal_id, cliente_id))
    if not cur.fetchone():
        raise RuntimeError("La sucursal no pertenece al cliente o está inactiva.")

def cargar_y_aplicar_mapeos_productos(archivo_bytes: bytes, nombre_archivo: str,
                                      cliente_id: int, sucursal_id: int | None) -> Dict[str, Any]:
    if not archivo_bytes:
        raise RuntimeError("Archivo vacío.")

    nombre = (nombre_archivo or "").lower()
    if nombre.endswith(".csv"):
        rows = _leer_csv(archivo_bytes)
    elif nombre.endswith(".xlsx"):
        rows = _leer_xlsx(archivo_bytes)
    else:
        raise RuntimeError("Formato no soportado. Usa .csv o .xlsx")

    filas = _estandarizar_columnas(rows)

    with db.obtener_conexion() as conn:
        with conn.cursor() as cur:
            por_sucursal = _verificar_modalidad_cliente(cur, cliente_id)
            if por_sucursal:
                if not sucursal_id:
                    raise RuntimeError("Este cliente usa bodega por sucursal: debes seleccionar la sucursal.")
                _validar_sucursal_pertenece(cur, sucursal_id, cliente_id)
            else:
                if sucursal_id:
                    # ignoramos sucursal si la mandan por error
                    sucursal_id = None

        # Ejecutar upsert según modalidad
        if por_sucursal:
            ins, act, om, errs = _upsert_bodega_por_sucursal(conn, sucursal_id, filas)
        else:
            ins, act, om, errs = _upsert_bodega_por_cliente(conn, cliente_id, filas)

    return {
        "insertados": ins,
        "actualizados": act,
        "omitidos": om,
        "errores": errs,
        "modo": "por_sucursal" if sucursal_id else "por_cliente"
    }
