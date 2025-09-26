# procesamiento_pedidos.py
# Parseo del PDF (filas de productos), sucursal y totales; normalización,
# emparejado por NOMBRE y ALIAS con BASE DE DATOS y utilidades.

from __future__ import annotations

import io
import re
import unicodedata
from decimal import Decimal
from typing import Any, Dict, List, Tuple
import difflib

import pdfplumber
import persistencia_postgresql as _pg  # obtener_conexion()

# ==============================
# Parámetros de emparejado
# ==============================

UMBRAL_SIMILITUD = 0.58  # si el score total supera este valor, se considera match
UMBRAL_HARD_SEQ  = 0.92  # aceptación dura por similitud de secuencia (SequenceMatcher)

# ==============================
# Utilidades de normalización
# ==============================

def normalizar_texto(s: str | None) -> str:
    """Quita tildes, pasa a minúsculas y limpia espacios redundantes."""
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
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?:\d+(?:[.,]\d+)?)\s+(?:\d+(?:[.,]\d+)?)$"
)
PATRON_FILA_SIN_UNIDAD = re.compile(
    r"^(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?:\d+(?:[.,]\d+)?)\s+(?:\d+(?:[.,]\d+)?)$"
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
      {'uni','desc','cant'} (cadenas tal como vienen en el PDF)
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
    print(f"{'Uni.':<10} | {'Descripción':<70} | {'Cant':>4}")
    print("-" * 90)
    for f in filas:
        desc = (f.get("desc") or "").strip()
        cant = f.get("cant")
        uni = f.get("uni") or ""
        print(f"{uni:<10} | {desc[:70]:<70} | {cant:>4}")

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
    patron = re.compile(
        rf"{titulo_regex}.*?(?:\$|\s)\s*([0-9][0-9\.\,]*|-)", re.IGNORECASE | re.DOTALL
    )
    m = patron.search(texto)
    if not m:
        titulo = re.compile(titulo_regex, re.IGNORECASE)
        lineas = texto.splitlines()
        for i, linea in enumerate(lineas):
            if titulo.search(linea):
                for j in range(1, max_saltos + 1):
                    if i + j < len(lineas):
                        x = re.search(r"([0-9][0-9\.\,]*|-)", lineas[i + j])
                        if x:
                            return x.group(1)
        return None
    return m.group(1)

def _limpiar_fecha_sucursal(sucursal: str) -> str:
    """
    Elimina fechas al final del nombre de sucursal.
    Ejemplo: "PATIO CC AVALON (CC AVALON PLAZA 3 LA AURORA SATELITE) 27/08/2025" 
    -> "PATIO CC AVALON (CC AVALON PLAZA 3 LA AURORA SATELITE)"
    """
    if not sucursal:
        return sucursal
    
    # Patrones para fechas al final:
    # - DD/MM/YYYY o DD/MM/YY
    # - DD-MM-YYYY o DD-MM-YY
    # - DD.MM.YYYY o DD.MM.YY
    # - Con o sin espacios antes de la fecha
    patrones_fecha = [
        r'\s+\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$',  # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        r'\s+\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\s*$'  # Con espacios adicionales al final
    ]
    
    sucursal_limpia = sucursal
    for patron in patrones_fecha:
        sucursal_limpia = re.sub(patron, '', sucursal_limpia, flags=re.IGNORECASE)
    
    return sucursal_limpia.strip()

def extraer_sucursal(pdf_en_bytes: bytes) -> Dict[str, Any]:
    """
    Devuelve:
      {
        "sucursal": "texto que viene en PDF (Solicita: …) sin fechas",
        "ruc": "RUC extraído del PDF si se encuentra",
        "orden_compra": "número de orden de compra del título del PDF",
        "responsable": "nombre del responsable extraído del PDF"
      }
    """
    texto = _texto_completo(pdf_en_bytes)

    # Sucursal (línea que inicia por 'Solicita:')
    sucursal = None
    for line in texto.splitlines():
        if re.search(r"^\s*Solicita\s*:", line, flags=re.IGNORECASE):
            sucursal = re.sub(r"^\s*Solicita\s*:\s*", "", line, flags=re.IGNORECASE).strip()
            # Limpiar fechas al final del nombre de sucursal
            sucursal = _limpiar_fecha_sucursal(sucursal)
            break

    # Buscar RUC en el texto del PDF
    ruc = None
    # Patrones comunes para RUC en PDFs
    ruc_patterns = [
        r'RUC[:\s]*(\d{10,13})',  # RUC: 1234567890123
        r'R\.U\.C[:\s]*(\d{10,13})',  # R.U.C: 1234567890123
        r'(\d{10,13})',  # Solo números de 10-13 dígitos
    ]
    
    for pattern in ruc_patterns:
        matches = re.findall(pattern, texto, re.IGNORECASE)
        if matches:
            # Tomar el primer RUC encontrado que tenga entre 10 y 13 dígitos
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                if 10 <= len(match) <= 13 and match.isdigit():
                    ruc = match
                    break
            if ruc:
                break

    # Extraer orden de compra del título del PDF
    orden_compra = None
    # Buscar patrones como "ORDEN DE COMPRA OS-0-0-4887" o similares
    orden_patterns = [
        r'ORDEN\s+DE\s+COMPRA\s+([A-Z0-9\-]+)',  # ORDEN DE COMPRA OS-0-0-4887
        r'ORDEN\s+DE\s+PEDIDO\s+([A-Z0-9\-]+)',  # ORDEN DE PEDIDO OS-0-0-4887
        r'PEDIDO\s+([A-Z0-9\-]+)',  # PEDIDO OS-0-0-4887
        r'OC\s+([A-Z0-9\-]+)',  # OC OS-0-0-4887
    ]
    
    for pattern in orden_patterns:
        matches = re.findall(pattern, texto, re.IGNORECASE)
        if matches:
            orden_compra = matches[0].strip()
            break

    # Extraer responsable del PDF
    responsable = None
    # Buscar patrones como "Solicita:", "Aprueba:", "Recibe:", "Analiza:"
    responsable_patterns = [
        r'Solicita[:\s]+([^\\n]+)',
        r'Aprueba[:\s]+([^\\n]+)',
        r'Recibe[:\s]+([^\\n]+)',
        r'Analiza[:\s]+([^\\n]+)',
    ]
    
    for pattern in responsable_patterns:
        matches = re.findall(pattern, texto, re.IGNORECASE)
        if matches:
            responsable = matches[0].strip()
            # Limpiar fechas al final del nombre del responsable
            responsable = _limpiar_fecha_sucursal(responsable)
            break

    return {
        "sucursal": sucursal,
        "ruc": ruc,
        "orden_compra": orden_compra,
        "responsable": responsable,
    }

def imprimir_resumen_pedido(res: Dict[str, Any]) -> None:
    print("========== 3) SUCURSAL ==========")
    print("\nResumen del pedido (extraído del PDF):")
    print(f"  Sucursal:        {res.get('sucursal') or '-'}")
    print(f"  RUC:             {res.get('ruc') or '-'}")
    print(f"  Orden de Compra: {res.get('orden_compra') or '-'}")
    print(f"  Responsable:     {res.get('responsable') or '-'}")
    print()

# ==============================
# Emparejado contra la BASE DE DATOS por NOMBRE
# ==============================

def solapamiento_tokens(a: str, b: str) -> float:
    """Métrica Jaccard (0..1) sobre conjuntos de tokens normalizados."""
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

def _resolver_sucursal_por_alias_y_ruc(cliente_id: int, alias_pdf: str | None, ruc_pdf: str | None) -> Dict[str, Any]:
    """
    Busca sucursal del cliente por alias y RUC.
    Lógica: 1) Buscar por alias, 2) Si hay múltiples con mismo alias, filtrar por RUC
    Devuelve dict {id, nombre} si encuentra coincidencia, o {} si no encontró.
    """
    if not alias_pdf and not ruc_pdf:
        return {}
    
    target_alias = normalizar_texto(alias_pdf) if alias_pdf else None
    target_ruc = ruc_pdf.strip() if ruc_pdf else None
    
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, nombre, COALESCE(alias, ''), COALESCE(ruc, '')
            FROM sucursales
            WHERE cliente_id = %s AND activo = TRUE;
        """, (cliente_id,))
        filas = cur.fetchall()

    # Paso 1: Buscar por alias exacto
    if target_alias:
        candidatos_alias = []
        for (sid, nombre, alias, ruc) in filas:
            alias_norm = normalizar_texto(alias)
            if alias_norm == target_alias:
                candidatos_alias.append((sid, nombre, ruc))
        
        if candidatos_alias:
            print(f"✅ Encontradas {len(candidatos_alias)} sucursal(es) con alias exacto: {alias_pdf}")
            
            # Paso 2: Si hay múltiples candidatos con el mismo alias, filtrar por RUC
            if len(candidatos_alias) > 1 and target_ruc:
                print(f"🔍 Múltiples sucursales con mismo alias, filtrando por RUC: {target_ruc}")
                for (sid, nombre, ruc) in candidatos_alias:
                    if ruc and ruc.strip() == target_ruc:
                        print(f"✅ Sucursal encontrada por alias + RUC: {alias_pdf} + {target_ruc} -> {nombre}")
                        return {"id": int(sid), "nombre": nombre}
                
                print(f"⚠️ No se encontró sucursal con alias '{alias_pdf}' y RUC '{target_ruc}'")
                return {}
            elif len(candidatos_alias) == 1:
                # Solo una sucursal con ese alias
                sid, nombre, ruc = candidatos_alias[0]
                print(f"✅ Sucursal encontrada por alias: {alias_pdf} -> {nombre}")
                return {"id": int(sid), "nombre": nombre}
            else:
                # Múltiples candidatos pero no se proporcionó RUC
                print(f"⚠️ Múltiples sucursales con alias '{alias_pdf}' pero no se proporcionó RUC para filtrar")
                return {}
    
    # Paso 3: Si no se encontró por alias exacto, buscar por similitud
    if target_alias:
        mejor_match = None
        mejor_puntaje = 0.0
        
        for (sid, nombre, alias, ruc) in filas:
            alias_norm = normalizar_texto(alias)
            if alias_norm:
                puntaje = solapamiento_tokens(target_alias, alias_norm)
                if puntaje > mejor_puntaje and puntaje > 0.6:  # Umbral de similitud
                    mejor_match = (sid, nombre, ruc)
                    mejor_puntaje = puntaje
        
        if mejor_match:
            sid, nombre, ruc = mejor_match
            print(f"✅ Sucursal encontrada por similitud de alias: {alias_pdf} -> {nombre} (puntaje: {mejor_puntaje:.2f})")
            return {"id": int(sid), "nombre": nombre}
    
    print(f"❌ No se encontró sucursal para alias: '{alias_pdf}' o RUC: '{ruc_pdf}'")
    return {}

# ---------- Catálogo global y similitud de nombres ----------

def _cargar_catalogo_productos() -> List[Dict[str, Any]]:
    """
    Carga catálogo global de productos activos.
    Devuelve: lista de dicts {id, sku, nombre, nombre_norm, tokens}
    """
    catalogo: List[Dict[str, Any]] = []
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, sku, nombre
            FROM productos
            WHERE activo = TRUE
        """)
        for pid, sku, nombre in cur.fetchall():
            nom = nombre or ""
            nom_norm = normalizar_texto(nom)
            catalogo.append({
                "id": int(pid),
                "sku": sku or "",
                "nombre": nom,
                "nombre_norm": nom_norm,
                "tokens": set(nom_norm.split())
            })
    return catalogo

def _cargar_alias_productos_por_cliente(cliente_id: int) -> List[Dict[str, Any]]:
    """
    Carga alias de productos para un cliente específico.
    Devuelve: lista de dicts {producto_id, alias_1, alias_2, alias_3, alias_norm, tokens}
    """
    alias_list: List[Dict[str, Any]] = []
    with _pg.obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT producto_id, alias_1, alias_2, alias_3
            FROM alias_productos
            WHERE cliente_id = %s
        """, (cliente_id,))
        for pid, alias_1, alias_2, alias_3 in cur.fetchall():
            # Procesar cada alias que no esté vacío
            for alias in [alias_1, alias_2, alias_3]:
                if alias and alias.strip():
                    alias_norm = normalizar_texto(alias)
                    alias_list.append({
                        "producto_id": int(pid),
                        "alias": alias.strip(),
                        "alias_norm": alias_norm,
                        "tokens": set(alias_norm.split())
                    })
    return alias_list

def _puntaje_similitud(q_norm: str, cand_norm: str, cand_tokens: set[str]) -> float:
    """
    Score combinado:
      0.6 * Jaccard(tokens) + 0.4 * SequenceMatcher
    Con pequeño bonus si hay prefijo/sufijo casi exacto.
    """
    tokens_q = set(q_norm.split())
    if not tokens_q or not cand_tokens:
        jacc = 0.0
    else:
        inter = len(tokens_q & cand_tokens)
        union = len(tokens_q | cand_tokens)
        jacc = inter / union if union else 0.0

    seq = difflib.SequenceMatcher(None, q_norm, cand_norm).ratio()

    score = 0.6 * jacc + 0.4 * seq

    # bonus por prefijo/sufijo cercano
    if cand_norm.startswith(q_norm) or q_norm.startswith(cand_norm):
        score += 0.03
    if cand_norm.endswith(q_norm) or q_norm.endswith(cand_norm):
        score += 0.02

    return min(score, 1.0)

def _buscar_producto_por_nombre_similar(catalogo: List[Dict[str, Any]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, float]:
    """
    Busca el producto cuyo NOMBRE o SKU coincide exactamente (100%) con el texto del PDF.
    Si no encuentra coincidencia exacta, devuelve None.
    Devuelve (producto_dict | None, score)
    """
    q_norm = normalizar_texto(texto_pdf or "")
    if not q_norm:
        return None, 0.0

    # Buscar SOLO por igualdad exacta (100%) - primero por SKU, luego por nombre
    for p in catalogo:
        # Buscar por SKU exacto
        if q_norm == normalizar_texto(p["sku"]):
            return p, 1.0
        # Buscar por nombre exacto
        if q_norm == p["nombre_norm"]:
            return p, 1.0

    # No se encontró coincidencia exacta
    return None, 0.0

def _buscar_producto_por_alias(alias_list: List[Dict[str, Any]], catalogo: List[Dict[str, Any]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, float]:
    """
    Busca el producto cuyo ALIAS coincide exactamente (100%) con el texto del PDF.
    Si no encuentra coincidencia exacta, devuelve None.
    Devuelve (producto_dict | None, score)
    """
    q_norm = normalizar_texto(texto_pdf or "")
    if not q_norm:
        return None, 0.0

    # Buscar SOLO por igualdad exacta (100%) en alias
    for alias_item in alias_list:
        if q_norm == alias_item["alias_norm"]:
            # Coincidencia exacta encontrada - buscar el producto correspondiente
            for p in catalogo:
                if p["id"] == alias_item["producto_id"]:
                    return p, 1.0

    # No se encontró coincidencia exacta
    return None, 0.0

def _buscar_producto_combinado(catalogo: List[Dict[str, Any]], alias_list: List[Dict[str, Any]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, float, str]:
    """
    Busca el producto por igualdad exacta (100%) primero por nombre, luego por alias.
    Si no encuentra coincidencia exacta, devuelve None.
    Devuelve (producto_dict | None, score, tipo_match)
    """
    # Primero intentar por nombre (igualdad exacta)
    prod_nombre, score_nombre = _buscar_producto_por_nombre_similar(catalogo, texto_pdf)
    if prod_nombre and score_nombre == 1.0:  # Coincidencia exacta
        return prod_nombre, score_nombre, "nombre"
    
    # Si no encuentra por nombre, intentar por alias (igualdad exacta)
    prod_alias, score_alias = _buscar_producto_por_alias(alias_list, catalogo, texto_pdf)
    if prod_alias and score_alias == 1.0:  # Coincidencia exacta
        return prod_alias, score_alias, "alias"
    
    # Si no encuentra por alias, intentar con unidad + descripción
    # Extraer unidad y descripción del texto
    partes = texto_pdf.strip().split(None, 1)  # Dividir en máximo 2 partes
    if len(partes) >= 2:
        unidad = partes[0]
        descripcion = partes[1]
        texto_combinado = f"{unidad} {descripcion}"
        
        # Buscar por nombre con el texto combinado (igualdad exacta)
        prod_combinado, score_combinado = _buscar_producto_por_nombre_similar(catalogo, texto_combinado)
        if prod_combinado and score_combinado == 1.0:  # Coincidencia exacta
            return prod_combinado, score_combinado, "nombre_combinado"
        
        # Buscar por alias con el texto combinado (igualdad exacta)
        prod_alias_combinado, score_alias_combinado = _buscar_producto_por_alias(alias_list, catalogo, texto_combinado)
        if prod_alias_combinado and score_alias_combinado == 1.0:  # Coincidencia exacta
            return prod_alias_combinado, score_alias_combinado, "alias_combinado"
    
    # No se encontró coincidencia exacta en ningún caso
    return None, 0.0, "sin_match"

# ---------- Mapas de bodega ----------

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

# ---------- Emparejador principal por NOMBRE ----------

def emparejar_filas_con_bd(
    filas: List[Dict[str, Any]],
    cliente_nombre: str = "Roldan",
    sucursal_alias: str | None = None,
    sucursal_ruc: str | None = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Enriquecer filas contra la BD:
      - Construye la consulta como: "UNIDAD + DESCRIPCIÓN" del PDF
      - Compara contra NOMBRE del producto en BD mediante similitud
      - Si no encuentra match, busca por ALIAS de productos
      - Si no encuentra por alias, intenta con unidad + descripción combinados
      - Toma bodega desde tablas de bodega (por cliente o por sucursal)
      - Resuelve sucursal del pedido desde alias y/o RUC del PDF -> nombre del sistema

    Devuelve (filas_enriquecidas, sucursal_dict, cliente_id)
    """
    cliente_id, usa_por_sucursal = _buscar_cliente_por_nombre(cliente_nombre)
    suc = _resolver_sucursal_por_alias_y_ruc(cliente_id, sucursal_alias, sucursal_ruc)

    # Catálogo global (nombres de productos)
    catalogo = _cargar_catalogo_productos()
    
    # Alias de productos para este cliente
    alias_list = _cargar_alias_productos_por_cliente(cliente_id)

    # Bodegas según modalidad
    mapa_bod_cli: Dict[int, str | None] = {}
    mapa_bod_suc: Dict[int, str | None] = {}
    if usa_por_sucursal and suc:
        mapa_bod_suc = _cargar_bodegas_por_sucursal(int(suc["id"]))
    else:
        mapa_bod_cli = _cargar_bodegas_por_cliente(cliente_id)

    enriquecidas: List[Dict[str, Any]] = []
    for f in filas:
        uni = (f.get("uni") or "").strip()
        desc = (f.get("desc") or "").strip()
        
        # Primero intentar solo con la descripción (sin unidad)
        prod, score, tipo_match = _buscar_producto_combinado(catalogo, alias_list, desc)
        
        # Si no encuentra con solo descripción, intentar con unidad + descripción
        if not prod and uni:
            consulta_completa = f"{uni} {desc}".strip()
            prod, score, tipo_match = _buscar_producto_combinado(catalogo, alias_list, consulta_completa)
        if prod:
            pid = prod["id"]
            sku = prod["sku"]
            bodega = (mapa_bod_suc.get(pid) if mapa_bod_suc else mapa_bod_cli.get(pid))
            enriquecidas.append({
                **f,
                "sku": sku,
                "bodega": bodega,
                "tipo_emparejado": tipo_match,
                "score_nombre": round(float(score), 4)
            })
        else:
            enriquecidas.append({
                **f,
                "sku": None,
                "bodega": None,
                "tipo_emparejado": "sin_match",
                "score_nombre": round(float(score or 0.0), 4)
            })

    return enriquecidas, (suc or {}), cliente_id

# ==============================
# Impresión de filas enriquecidas
# ==============================

def imprimir_filas_emparejadas(filas_enriquecidas: List[Dict[str, Any]]) -> None:
    if not filas_enriquecidas:
        print("⚠️ No hay filas emparejadas.")
        return
    print("========== 2) FILAS ENRIQUECIDAS ==========")
    print(f"{'Uni.':<8} | {'Descripción':<58} | {'Cant':>4} | {'SKU':<10} | {'Bod':>3} | {'Score':>5} | {'Match':<16}")
    print("-" * 120)
    for f in filas_enriquecidas:
        desc = (f.get("desc") or "").strip()
        cant = f.get("cant") or ""
        sku  = f.get("sku") or ""
        bod  = f.get("bodega") or ""
        tip  = f.get("tipo_emparejado") or ""
        sc   = f.get("score_nombre")
        print(f"{(f.get('uni') or ''):<8} | {desc[:58]:<58} | {cant:>4} | {sku:<10} | {str(bod):>3} | {str(sc or ''):>5} | {tip:<16}")
