# procesamiento_pedidos.py
# Parseo del PDF (filas de productos), sucursal y totales; normalización,
# emparejado con BASE DE DATOS (alias por cliente/sucursal) y utilidades.
#
# NOTA: Se eliminó el emparejado contra CSV. Para compatibilidad con código
#       existente, se deja un "shim" emparejar_filas_con_catalogo() que delega
#       a la base de datos con cliente fijo (por ahora "Roldan").

from __future__ import annotations

import io
import re
import unicodedata
from decimal import Decimal
from typing import Any, Dict, List, Tuple

import pdfplumber
import persistencia_postgresql as _pg  # obtener_conexion()

# ==============================
# Utilidades de normalización
# ==============================

def normalizar_texto(s: str | None) -> str:
    """Quita tildes, pasa a minúsculas, limpia espacios redundantes."""
    if not s:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s

def to_decimal_es(x: str | float | int | None) -> Decimal | None:
    """Convierte '1.234,56' o '1234.56' a Decimal. None si no aplica."""
    if x is None: 
        return None
    s = str(x).strip()
    if not s or s == "-":
        return None
    # Si hay coma y punto, asumir formato ES: miles con punto, decimales con coma
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

def fmt2(x: Decimal | None) -> str:
    return "-" if x is None else f"{x:.2f}"

# ==============================
# Parseo de filas del PDF
# ==============================

PALABRAS_UNIDAD = {
    "Unidad", "UNIDAD", "RESMA", "Caja", "CAJA", "Rollo", "ROLLO",
    "Paquete", "PAQUETE", "Funda", "FUNDA", "Galon", "GALON",
    "Kilo", "KILO", "Par", "PAR", "Unidad."
}

PATRON_FILA_CON_UNIDAD = re.compile(
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)
PATRON_FILA_SIN_UNIDAD = re.compile(
    r"^(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

PALABRAS_OMITIR = (
    "Uni. Descripción", "Subtotal", "TOTAL", "IVA", "Proveedor",
    "ORDEN DE COMPRA", "Fecha:", "Dirección:", "Teléfono:", "Política:",
    "Razón", "RUC:", "E-mail", "Datos de facturación", "Aprueba:",
    "Recibe:", "Analiza:", "Solicita:"
)

def es_linea_omitible(linea: str) -> bool:
    s = (linea or "").strip()
    if not s:
        return True
    return any(p in s for p in PALABRAS_OMITIR)

def extraer_filas_pdf(pdf_en_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Lee el PDF y extrae filas tipo:
      {'uni','desc','cant','puni','ptotal'} (cadenas tal como vienen en el PDF)
    """
    filas: List[Dict[str, Any]] = []
    unidad_en_espera: str | None = None

    with pdfplumber.open(io.BytesIO(pdf_en_bytes)) as pdf:
        for page in pdf.pages:
            try:
                texto = page.extract_text() or ""
            except Exception:
                continue
            for raw in texto.splitlines():
                linea = raw.strip()
                if es_linea_omitible(linea):
                    continue

                # Caso 1: con unidad al inicio
                m1 = PATRON_FILA_CON_UNIDAD.match(linea)
                if m1:
                    d = m1.groupdict()
                    filas.append(d)
                    unidad_en_espera = None
                    continue

                # Detectar palabra de unidad suelta al principio
                if not unidad_en_espera:
                    token0 = (linea.split() or [""])[0]
                    if token0 in PALABRAS_UNIDAD:
                        # guardar y esperar que la siguiente línea sea la fila sin 'uni'
                        unidad_en_espera = token0
                        continue

                # Caso 2: sin unidad (usar la última detectada)
                m2 = PATRON_FILA_SIN_UNIDAD.match(linea)
                if m2 and unidad_en_espera:
                    d = m2.groupdict()
                    d["uni"] = unidad_en_espera
                    filas.append(d)
                    unidad_en_espera = None
                    continue

    return filas

def imprimir_filas(filas: List[Dict[str, Any]]) -> None:
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return
    print(f"{'Uni.':<10} | {'Descripción':<70} | {'Cant':>4} | {'P. Uni':>8} | {'P. Total':>9}")
    print("-" * 110)
    for f in filas:
        desc = (f.get("desc") or "").strip()
        cant = f.get("cant")
        puni = str(f.get("puni") or "").replace(",", ".")
        ptotal = str(f.get("ptotal") or "").replace(",", ".")
        uni = f.get("uni") or ""
        print(f"{uni:<10} | {desc[:70]:<70} | {cant:>4} | {puni:>8} | {ptotal:>9}")

# ==============================
# Parseo de sucursal y totales
# ==============================

def _texto_completo(pdf_en_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_en_bytes)) as pdf:
        partes = []
        for p in pdf.pages:
            try:
                partes.append(p.extract_text() or "")
            except Exception:
                continue
    return "\n".join(partes)

def _buscar_valor(titulo_regex: str, texto: str, max_saltos: int = 2) -> str | None:
    """
    Busca un valor numérico tipo 1.234,56 AFTER un título "Subtotal", "IVA 0%", "TOTAL"...
    """
    patron = re.compile(
        rf"{titulo_regex}.*?(?:\$|\s)\s*([0-9][0-9\.\,]*|-)", re.IGNORECASE | re.DOTALL
    )
    m = patron.search(texto)
    if not m:
        # búsqueda tolerante a saltos de línea
        titulo = re.compile(titulo_regex, re.IGNORECASE)
        for i, linea in enumerate(texto.splitlines()):
            if titulo.search(linea):
                for j in range(1, max_saltos + 1):
                    if i + j < len(texto.splitlines()):
                        x = re.search(r"([0-9][0-9\.\,]*|-)", texto.splitlines()[i + j])
                        if x:
                            return x.group(1)
        return None
    return m.group(1)

def extraer_sucursal_y_totales(pdf_en_bytes: bytes) -> Dict[str, Any]:
    """
    Devuelve:
      {
        "sucursal": "texto que viene en PDF (Solicita: …)",
        "subtotal_bruto": Decimal|None,
        "descuento": Decimal|None,
        "subtotal_neto": Decimal|None,
        "iva_0": Decimal|None,
        "iva_15": Decimal|None,
        "total": Decimal|None,
      }
    """
    texto = _texto_completo(pdf_en_bytes)

    # Sucursal (línea que inicia por 'Solicita:')
    sucursal = None
    for line in texto.splitlines():
        if re.search(r"^\s*Solicita\s*:", line, flags=re.IGNORECASE):
            sucursal = re.sub(r"^\s*Solicita\s*:\s*", "", line, flags=re.IGNORECASE).strip()
            break

    # Totales
    # Algunos PDFs traen dos "Subtotal": bruto y neto
    subtotales_raw = re.findall(
        r"Subtotal(?:[^\S\r\n]|\n){0,2}\$?\s*([0-9][0-9\.\,]*|-)",
        texto,
        flags=re.IGNORECASE
    )
    raw_descuento = _buscar_valor(r"Descuento", texto, max_saltos=2)
    raw_iva0      = _buscar_valor(r"IVA\s*0%",   texto, max_saltos=2)
    raw_iva15     = _buscar_valor(r"IVA\s*15%",  texto, max_saltos=2)
    raw_total     = _buscar_valor(r"\bTOTAL\b",  texto, max_saltos=3)

    subtotal_bruto = to_decimal_es(subtotales_raw[0]) if len(subtotales_raw) >= 1 else None
    subtotal_neto  = to_decimal_es(subtotales_raw[1]) if len(subtotales_raw) >= 2 else None

    descuento = to_decimal_es(raw_descuento)
    iva_0     = Decimal("0") if (raw_iva0 is None or raw_iva0 == "-") else to_decimal_es(raw_iva0)
    iva_15    = to_decimal_es(raw_iva15)
    total     = to_decimal_es(raw_total)

    return {
        "sucursal": sucursal,
        "subtotal_bruto": subtotal_bruto,
        "descuento": descuento,
        "subtotal_neto": subtotal_neto,
        "iva_0": iva_0,
        "iva_15": iva_15,
        "total": total,
    }

def imprimir_resumen_pedido(res: Dict[str, Any]) -> None:
    print("========== 3) SUCURSAL Y TOTALES ==========")
    print("\nResumen del pedido (extraído del PDF):")
    print(f"  Sucursal:        {res.get('sucursal') or '-'}")
    print(f"  Subtotal bruto:  {fmt2(res.get('subtotal_bruto'))}")
    print(f"  Descuento:       {fmt2(res.get('descuento'))}")
    print(f"  Subtotal neto:   {fmt2(res.get('subtotal_neto'))}")
    print(f"  IVA 0%:          {fmt2(res.get('iva_0'))}")
    print(f"  IVA 15%:         {fmt2(res.get('iva_15'))}")
    print(f"  TOTAL:           {fmt2(res.get('total'))}")
    print()

# ==============================
# Emparejado contra la BASE DE DATOS
# ==============================

def solapamiento_tokens(a: str, b: str) -> float:
    """Métrica sencilla de solapamiento (0..1) por tokens."""
    ta = set(normalizar_texto(a).split())
    tb = set(normalizar_texto(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0

def _buscar_cliente_por_nombre(nombre: str) -> Tuple[int, bool]:
    """Devuelve (cliente_id, usa_bodega_por_sucursal). Lanza si no existe."""
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, COALESCE(usa_bodega_por_sucursal, FALSE)
            FROM clientes
            WHERE upper(nombre) = upper(%s)
            LIMIT 1;
        """, (nombre,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Cliente '{nombre}' no encontrado.")
        return int(row[0]), bool(row[1])

def _resolver_sucursal_por_alias(cliente_id: int, alias_pdf: str | None) -> Dict[str, Any]:
    """
    Busca sucursal del cliente por alias (o nombre) que viene en el PDF.
    Devuelve dict {id, nombre} o {} si no encontró.
    """
    if not alias_pdf:
        return {}
    target = normalizar_texto(alias_pdf)
    mejor = None
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, nombre, COALESCE(alias, '')
            FROM sucursales
            WHERE cliente_id = %s AND activo = TRUE;
        """, (cliente_id,))
        filas = cur.fetchall()

    # Igualdad exacta (normalizada) contra alias o nombre
    for (sid, nombre, alias) in filas:
        if normalizar_texto(alias) == target or normalizar_texto(nombre) == target:
            return {"id": int(sid), "nombre": nombre}

    # Contención con mejor solapamiento
    max_sc = -1.0
    for (sid, nombre, alias) in filas:
        a = normalizar_texto(alias); n = normalizar_texto(nombre)
        for cand in (a, n):
            sc = solapamiento_tokens(target, cand)
            if sc > max_sc and (target in cand or cand in target):
                mejor = {"id": int(sid), "nombre": nombre}
                max_sc = sc

    return mejor or {}

def _cargar_alias_productos_cliente(cliente_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Devuelve índice: alias_norm -> [ {producto_id, sku, nombre, alias_original}, ... ]
    """
    idx: Dict[str, List[Dict[str, Any]]] = {}
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT p.id, p.sku, p.nombre, ap.alias
            FROM alias_productos ap
            JOIN productos p ON p.id = ap.producto_id
            WHERE ap.cliente_id = %s
            ORDER BY ap.id ASC;
        """, (cliente_id,))
        for (pid, sku, nombre, alias) in cur.fetchall():
            clave = normalizar_texto(alias or "")
            idx.setdefault(clave, []).append({
                "producto_id": int(pid),
                "sku": sku or "",
                "nombre": nombre or "",
                "alias_original": alias or ""
            })
    return idx

def _cargar_bodegas_por_cliente(cliente_id: int) -> Dict[int, str | None]:
    """producto_id -> bodega (para clientes que NO usan bodega por sucursal)"""
    mapa: Dict[int, str | None] = {}
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT producto_id, bodega
            FROM bodegas_producto_por_cliente
            WHERE cliente_id = %s
            ORDER BY id ASC;
        """, (cliente_id,))
        for (pid, bod) in cur.fetchall():
            mapa[int(pid)] = bod or None
    return mapa

def _cargar_bodegas_por_sucursal(sucursal_id: int) -> Dict[int, str | None]:
    """producto_id -> bodega (para clientes que SÍ usan bodega por sucursal)"""
    mapa: Dict[int, str | None] = {}
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT producto_id, bodega
            FROM bodegas_producto_por_sucursal
            WHERE sucursal_id = %s
            ORDER BY id ASC;
        """, (sucursal_id,))
        for (pid, bod) in cur.fetchall():
            mapa[int(pid)] = bod or None
    return mapa

def _buscar_en_alias(alias_idx: Dict[str, List[Dict[str, Any]]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, str]:
    """
    Intenta match por:
    1) Igualdad exacta normalizada
    2) Contención (A in B o B in A) con mejor solapamiento
    Devuelve (producto_dict, tipo)
    """
    q = normalizar_texto(texto_pdf or "")
    if not q:
        return None, "sin_match"
    # Exacto
    if q in alias_idx and alias_idx[q]:
        return alias_idx[q][0], "exacto"

    # Contiene: tomamos el alias con mayor solapamiento de tokens
    mejor, max_sol = None, -1.0
    for clave, lst in alias_idx.items():
        if q in clave or clave in q:
            sol = solapamiento_tokens(q, clave)
            if sol > max_sol:
                max_sol = sol
                mejor = lst[0]
    return (mejor, "contiene") if mejor else (None, "sin_match")

def emparejar_filas_con_bd(
    filas: List[Dict[str, Any]],
    cliente_nombre: str = "Roldan",
    sucursal_alias: str | None = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enriquecer filas contra la BD del cliente:
      - Usar alias_productos para asignar SKU
      - Tomar bodega desde bodegas_producto_por_cliente o ..._por_sucursal según el cliente
      - Resolver sucursal del pedido desde alias de PDF -> nombre del sistema

    Devuelve (filas_enriquecidas, sucursal_dict)
    """
    cliente_id, usa_por_sucursal = _buscar_cliente_por_nombre(cliente_nombre)
    suc = _resolver_sucursal_por_alias(cliente_id, sucursal_alias)
    alias_idx = _cargar_alias_productos_cliente(cliente_id)

    # Bodegas según modalidad
    mapa_bod_cli: Dict[int, str | None] = {}
    mapa_bod_suc: Dict[int, str | None] = {}
    if usa_por_sucursal and suc:
        mapa_bod_suc = _cargar_bodegas_por_sucursal(int(suc["id"]))
    else:
        mapa_bod_cli = _cargar_bodegas_por_cliente(cliente_id)

    enriquecidas: List[Dict[str, Any]] = []
    for f in filas:
        prod, tipo = _buscar_en_alias(alias_idx, f.get("desc", ""))
        if prod:
            pid = prod["producto_id"]
            sku = prod["sku"]
            bodega = (mapa_bod_suc.get(pid) if mapa_bod_suc else mapa_bod_cli.get(pid))
            enriquecidas.append({
                **f,
                "sku": sku,
                "bodega": bodega,
                "tipo_emparejado": tipo
            })
        else:
            enriquecidas.append({
                **f,
                "sku": None,
                "bodega": None,
                "tipo_emparejado": "sin_match"
            })

    return enriquecidas, (suc or {})

# ==============================
# Compatibilidad con código antiguo (CSV)
# ==============================

def emparejar_filas_con_catalogo(filas: List[Dict[str, Any]], ruta_csv: str | None = None) -> List[Dict[str, Any]]:
    """
    Compatibilidad: antes emparejábamos con CSV.
    Ahora delegamos al emparejado con BD (cliente fijo "Roldan").
    Devuelve solo la lista de filas enriquecidas.
    """
    enriquecidas, _ = emparejar_filas_con_bd(filas, cliente_nombre="Roldan", sucursal_alias=None)
    return enriquecidas

# ==============================
# Impresión de filas enriquecidas
# ==============================

def imprimir_filas_emparejadas(filas_enriquecidas: List[Dict[str, Any]]) -> None:
    if not filas_enriquecidas:
        print("⚠️ No hay filas emparejadas.")
        return
    print("========== 2) FILAS ENRIQUECIDAS ==========")
    print(f"{'Uni.':<8} | {'Descripción':<60} | {'Cant':>4} | {'SKU':<10} | {'Bod':>3} | {'Match':<10}")
    print("-" * 110)
    for f in filas_enriquecidas:
        desc = (f.get("desc") or "").strip()
        cant = f.get("cant") or ""
        sku  = f.get("sku") or ""
        bod  = f.get("bodega") or ""
        tip  = f.get("tipo_emparejado") or ""
        print(f"{(f.get('uni') or ''):<8} | {desc[:60]:<60} | {cant:>4} | {sku:<10} | {str(bod):>3} | {tip:<10}")

# ==============================
# CSV opcional para auditoría (NO usa catálogo CSV)
# ==============================

def guardar_asignaciones_csv(filas_enriquecidas: List[Dict[str, Any]], ruta_salida: str = "pedido_asignado.csv") -> None:
    """
    Guarda un CSV con las asignaciones resultantes (para auditoría).
    No usa ningún catálogo CSV; solo vuelca lo enriquecido.
    Columnas: uni, desc, cant, puni, ptotal, sku, bodega, tipo_emparejado
    """
    import csv
    columnas = ["uni","desc","cant","puni","ptotal","sku","bodega","tipo_emparejado"]
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for r in filas_enriquecidas:
            fila = {k: r.get(k) for k in columnas}
            w.writerow(fila)
    print(f"💾 Guardado CSV: {ruta_salida}")
