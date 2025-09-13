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

def extraer_sucursal(pdf_en_bytes: bytes) -> Dict[str, Any]:
    """
    Devuelve:
      {
        "sucursal": "texto que viene en PDF (Solicita: …)",
      }
    """
    texto = _texto_completo(pdf_en_bytes)

    # Sucursal (línea que inicia por 'Solicita:')
    sucursal = None
    for line in texto.splitlines():
        if re.search(r"^\s*Solicita\s*:", line, flags=re.IGNORECASE):
            sucursal = re.sub(r"^\s*Solicita\s*:\s*", "", line, flags=re.IGNORECASE).strip()
            break

    return {
        "sucursal": sucursal,
    }

def imprimir_resumen_pedido(res: Dict[str, Any]) -> None:
    print("========== 3) SUCURSAL ==========")
    print("\nResumen del pedido (extraído del PDF):")
    print(f"  Sucursal:        {res.get('sucursal') or '-'}")
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
    Busca el producto cuyo NOMBRE es más parecido al texto del PDF (unidad + desc).
    Devuelve (producto_dict | None, score)
    """
    q_norm = normalizar_texto(texto_pdf or "")
    if not q_norm:
        return None, 0.0

    mejor, mejor_sc = None, -1.0
    for p in catalogo:
        sc = _puntaje_similitud(q_norm, p["nombre_norm"], p["tokens"])
        # aceptación dura
        if sc < UMBRAL_SIMILITUD and difflib.SequenceMatcher(None, q_norm, p["nombre_norm"]).ratio() >= UMBRAL_HARD_SEQ:
            sc = UMBRAL_SIMILITUD + 0.001
        if sc > mejor_sc:
            mejor_sc = sc
            mejor = p

    if mejor and mejor_sc >= UMBRAL_SIMILITUD:
        return mejor, mejor_sc
    return None, mejor_sc

def _buscar_producto_por_alias(alias_list: List[Dict[str, Any]], catalogo: List[Dict[str, Any]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, float]:
    """
    Busca el producto cuyo ALIAS es más parecido al texto del PDF.
    Devuelve (producto_dict | None, score)
    """
    q_norm = normalizar_texto(texto_pdf or "")
    if not q_norm:
        return None, 0.0

    mejor, mejor_sc = None, -1.0
    for alias_item in alias_list:
        sc = _puntaje_similitud(q_norm, alias_item["alias_norm"], alias_item["tokens"])
        # aceptación dura
        if sc < UMBRAL_SIMILITUD and difflib.SequenceMatcher(None, q_norm, alias_item["alias_norm"]).ratio() >= UMBRAL_HARD_SEQ:
            sc = UMBRAL_SIMILITUD + 0.001
        if sc > mejor_sc:
            mejor_sc = sc
            # Buscar el producto correspondiente en el catálogo
            for p in catalogo:
                if p["id"] == alias_item["producto_id"]:
                    mejor = p
                    break

    if mejor and mejor_sc >= UMBRAL_SIMILITUD:
        return mejor, mejor_sc
    return None, mejor_sc

def _buscar_producto_combinado(catalogo: List[Dict[str, Any]], alias_list: List[Dict[str, Any]], texto_pdf: str) -> Tuple[Dict[str, Any] | None, float, str]:
    """
    Busca el producto primero por nombre, luego por alias si no encuentra match.
    Devuelve (producto_dict | None, score, tipo_match)
    """
    # Primero intentar por nombre
    prod_nombre, score_nombre = _buscar_producto_por_nombre_similar(catalogo, texto_pdf)
    if prod_nombre and score_nombre >= UMBRAL_SIMILITUD:
        return prod_nombre, score_nombre, "nombre"
    
    # Si no encuentra por nombre, intentar por alias
    prod_alias, score_alias = _buscar_producto_por_alias(alias_list, catalogo, texto_pdf)
    if prod_alias and score_alias >= UMBRAL_SIMILITUD:
        return prod_alias, score_alias, "alias"
    
    # Si no encuentra por alias, intentar con unidad + descripción
    # Extraer unidad y descripción del texto
    partes = texto_pdf.strip().split(None, 1)  # Dividir en máximo 2 partes
    if len(partes) >= 2:
        unidad = partes[0]
        descripcion = partes[1]
        texto_combinado = f"{unidad} {descripcion}"
        
        # Buscar por nombre con el texto combinado
        prod_combinado, score_combinado = _buscar_producto_por_nombre_similar(catalogo, texto_combinado)
        if prod_combinado and score_combinado >= UMBRAL_SIMILITUD:
            return prod_combinado, score_combinado, "nombre_combinado"
        
        # Buscar por alias con el texto combinado
        prod_alias_combinado, score_alias_combinado = _buscar_producto_por_alias(alias_list, catalogo, texto_combinado)
        if prod_alias_combinado and score_alias_combinado >= UMBRAL_SIMILITUD:
            return prod_alias_combinado, score_alias_combinado, "alias_combinado"
    
    # Devolver el mejor score encontrado (aunque no supere el umbral)
    mejor_score = max(score_nombre, score_alias)
    mejor_producto = prod_nombre if score_nombre >= score_alias else prod_alias
    tipo_mejor = "nombre" if score_nombre >= score_alias else "alias"
    
    return mejor_producto, mejor_score, tipo_mejor

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
    sucursal_alias: str | None = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
    """
    Enriquecer filas contra la BD:
      - Construye la consulta como: "UNIDAD + DESCRIPCIÓN" del PDF
      - Compara contra NOMBRE del producto en BD mediante similitud
      - Si no encuentra match, busca por ALIAS de productos
      - Si no encuentra por alias, intenta con unidad + descripción combinados
      - Toma bodega desde tablas de bodega (por cliente o por sucursal)
      - Resuelve sucursal del pedido desde alias del PDF -> nombre del sistema

    Devuelve (filas_enriquecidas, sucursal_dict, cliente_id)
    """
    cliente_id, usa_por_sucursal = _buscar_cliente_por_nombre(cliente_nombre)
    suc = _resolver_sucursal_por_alias(cliente_id, sucursal_alias)

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
        consulta = (f"{uni} {desc}").strip() if uni else desc

        # Usar la nueva función de búsqueda combinada
        prod, score, tipo_match = _buscar_producto_combinado(catalogo, alias_list, consulta)
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
