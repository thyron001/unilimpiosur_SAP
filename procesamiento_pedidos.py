# procesamiento_pedidos.py
# Parseo del PDF (filas de productos), sucursal y totales; normalización, emparejado con catálogo y utilidades.

import os
import io
import re
import pdfplumber
import pandas as pd
import unicodedata
from decimal import Decimal

# ===== Configurable por entorno =====
RUTA_CATALOGO = os.getenv("PRODUCT_CSV", "productos_roldan.csv")

# ======== UTILIDADES DECIMALES (ES) ========

_DECIM_SAN = re.compile(r"[^0-9,.\-]")

def to_decimal_es(valor: str | None) -> Decimal | None:
    """Convierte '$1.234,56' o '168,09' a Decimal(1234.56). Devuelve None si no aplica."""
    if valor is None:
        return None
    s = _DECIM_SAN.sub("", str(valor)).strip()
    if s == "" or s == "-":
        return None
    # Solo coma -> decimal
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

def fmt2(x: Decimal | None) -> str:
    return "-" if x is None else f"{x:.2f}"

# ======== PARSEADOR DEL PDF: FILAS ========

PALABRAS_UNIDAD = {
    "Unidad", "RESMA", "Caja", "Rollo", "Paquete",
    "Funda", "Galon", "Kilo", "Par", "Unidad."
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

def limpiar_unidad(u: str) -> str:
    return (u or "").rstrip(".")

def extraer_filas_pdf(pdf_en_bytes: bytes) -> list[dict]:
    """
    Devuelve filas de la tabla del PDF con forma:
    { 'uni': str, 'desc': str, 'cant': str, 'puni': str, 'ptotal': str }
    """
    filas: list[dict] = []
    with pdfplumber.open(io.BytesIO(pdf_en_bytes)) as pdf:
        unidad_en_espera = None
        for pagina in pdf.pages:
            texto = pagina.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for bruta in texto.splitlines():
                linea = bruta.strip()
                if es_linea_omitible(linea):
                    continue

                if linea in PALABRAS_UNIDAD:
                    unidad_en_espera = limpiar_unidad(linea)
                    continue

                m = PATRON_FILA_CON_UNIDAD.match(linea)
                if m and limpiar_unidad(m.group("uni")) in PALABRAS_UNIDAD:
                    d = m.groupdict()
                    d["uni"] = limpiar_unidad(d["uni"])
                    filas.append(d)
                    unidad_en_espera = None
                    continue

                if unidad_en_espera:
                    m2 = PATRON_FILA_SIN_UNIDAD.match(linea)
                    if m2:
                        d = m2.groupdict()
                        d["uni"] = unidad_en_espera
                        filas.append(d)
                        unidad_en_espera = None
                        continue
    return filas

def imprimir_filas(filas: list[dict]) -> None:
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return
    print(f"{'Uni.':<10} | {'Descripción':<70} | {'Cant':>4} | {'P. Uni':>8} | {'P. Total':>9}")
    print("-" * 110)
    for f in filas:
        desc = (f["desc"] or "").strip()
        cant = f["cant"]
        puni = f["puni"].replace(",", ".")
        ptotal = f["ptotal"].replace(",", ".")
        uni = f["uni"]
        print(f"{uni:<10} | {desc[:70]:<70} | {cant:>4} | {puni:>8} | {ptotal:>9}")

# ======== PARSEADOR DEL PDF: SUCURSAL Y TOTALES ========

def _texto_completo(pdf_en_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_en_bytes)) as pdf:
        textos = [(p.extract_text(x_tolerance=2, y_tolerance=2) or "") for p in pdf.pages]
    return "\n".join(textos)

def _buscar_valor(label_regex: str, texto: str, max_saltos: int = 2) -> str | None:
    """
    Busca un valor numérico justo a la derecha/abajo de la etiqueta.
    Acepta hasta 'max_saltos' saltos de línea entre etiqueta y valor.
    """
    # valor como números con . y , o un '-'
    VAL = r"\$?\s*([0-9][0-9\.\,]*|-)"
    patron = rf"{label_regex}(?:[^\S\r\n]|\n){{0,{max_saltos}}}{VAL}"
    m = re.search(patron, texto, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None

def extraer_sucursal_y_totales(pdf_en_bytes: bytes) -> dict:
    """
    Extrae:
      sucursal, subtotal_bruto, descuento, subtotal_neto, iva_0, iva_15, total
    con tolerancia a saltos de línea entre etiqueta y valor.
    """
    texto = _texto_completo(pdf_en_bytes)

    # --- Sucursal (línea "Solicita:" o siguiente línea) ---
    sucursal = None
    m = re.search(r"Solicita:\s*(.+)", texto, re.IGNORECASE)
    if m:
        sucursal = m.group(1).strip()
    else:
        lineas = [l.strip() for l in texto.splitlines()]
        for i, l in enumerate(lineas):
            if l.upper().startswith("SOLICITA:"):
                resto = l.split(":", 1)[-1].strip()
                if resto:
                    sucursal = resto
                else:
                    for j in range(i + 1, min(i + 3, len(lineas))):
                        if lineas[j]:
                            sucursal = lineas[j]
                            break
                break

    # --- Totales del panel derecho ---
    # Dos "Subtotal": bruto (antes de descuento) y neto (después de descuento)
    subtotales_raw = re.findall(
        r"Subtotal(?:[^\S\r\n]|\n){0,2}\$?\s*([0-9][0-9\.\,]*|-)",
        texto,
        flags=re.IGNORECASE
    )
    raw_descuento = _buscar_valor(r"Descuento", texto, max_saltos=2)
    raw_iva0      = _buscar_valor(r"IVA\s*0%",   texto, max_saltos=2)
    raw_iva15     = _buscar_valor(r"IVA\s*15%",  texto, max_saltos=2)
    raw_total     = _buscar_valor(r"\bTOTAL\b",  texto, max_saltos=2)

    subtotal_bruto = to_decimal_es(subtotales_raw[0]) if len(subtotales_raw) >= 1 else None
    subtotal_neto  = to_decimal_es(subtotales_raw[1]) if len(subtotales_raw) >= 2 else None

    descuento = to_decimal_es(raw_descuento)
    # En muchos PDFs, IVA 0% aparece como '-'
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

def imprimir_resumen_pedido(res: dict) -> None:
    print("\nResumen del pedido (extraído del PDF):")
    print(f"  Sucursal:        {res.get('sucursal') or '-'}")
    print(f"  Subtotal bruto:  {fmt2(res.get('subtotal_bruto'))}")
    print(f"  Descuento:       {fmt2(res.get('descuento'))}")
    print(f"  Subtotal neto:   {fmt2(res.get('subtotal_neto'))}")
    print(f"  IVA 0%:          {fmt2(res.get('iva_0'))}")
    print(f"  IVA 15%:         {fmt2(res.get('iva_15'))}")
    print(f"  TOTAL:           {fmt2(res.get('total'))}")

# ======== EMPAREJADO CON CATÁLOGO ========

_CATALOGO_CACHE: pd.DataFrame | None = None

def normalizar_texto(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def solapamiento_tokens(a: str, b: str) -> int:
    toks = [t for t in a.split() if len(t) >= 3]
    bset = set(b.split())
    return sum(1 for t in toks if t in bset)

def cargar_catalogo(ruta: str = RUTA_CATALOGO) -> pd.DataFrame:
    global _CATALOGO_CACHE
    if _CATALOGO_CACHE is not None:
        return _CATALOGO_CACHE
    df = pd.read_csv(ruta, dtype=str)
    requeridas = [
        "Unidad",
        "NOMBRE DE ARTICULO EN LA ORDEN",
        "CODIGO DE PRODUCTO SAP",
        "BODEGA DESDE DONDE SE DESPACHA",
    ]
    for c in requeridas:
        if c not in df.columns:
            raise RuntimeError(f"CSV de catálogo no tiene la columna requerida: {c}")
    df["nombre_norm"] = df["NOMBRE DE ARTICULO EN LA ORDEN"].map(normalizar_texto)
    df["unidad_norm"] = df["Unidad"].map(normalizar_texto)
    _CATALOGO_CACHE = df
    return _CATALOGO_CACHE

def construir_indice_nombres(df: pd.DataFrame) -> dict[str, list[int]]:
    idx: dict[str, list[int]] = {}
    for i, s in enumerate(df["nombre_norm"]):
        idx.setdefault(s, []).append(i)
    return idx

def emparejar_filas_con_catalogo(filas: list[dict], ruta_csv: str = RUTA_CATALOGO) -> list[dict]:
    """
    Enriquecer filas con:
      - sku
      - bodega
      - tipo_emparejado in {'exacto','contiene','contiene+unidad','ambiguo','sin_match'}
      - candidatos (opcional)
    """
    df = cargar_catalogo(ruta_csv)
    indice = construir_indice_nombres(df)

    enriquecidas: list[dict] = []
    for f in filas:
        desc_n = normalizar_texto(f.get("desc", ""))
        uni_n  = normalizar_texto(f.get("uni", ""))

        sku = None
        bodega = None
        tipo = "sin_match"
        candidatos: list[str] = []

        if desc_n in indice:
            posibles = indice[desc_n]
        else:
            posibles = [
                i for i, nm in enumerate(df["nombre_norm"])
                if desc_n and (desc_n in nm or nm in desc_n)
            ]

        if posibles:
            if uni_n:
                por_unidad = [i for i in posibles if df.loc[i, "unidad_norm"] == uni_n]
                if por_unidad:
                    posibles = por_unidad
                    tipo = "contiene+unidad" if tipo != "exacto" else "exacto"
                else:
                    por_nombre_unidad = [i for i in posibles if uni_n and uni_n in df.loc[i, "nombre_norm"]]
                    if por_nombre_unidad:
                        posibles = por_nombre_unidad
                        tipo = "contiene+unidad"

            if len(posibles) > 1:
                overlaps = [(i, solapamiento_tokens(desc_n, df.loc[i, "nombre_norm"])) for i in posibles]
                max_ol = max(o for _, o in overlaps)
                mejores = [i for i, o in overlaps if o == max_ol]
                if len(mejores) == 1:
                    posibles = mejores
                else:
                    candidatos = [df.loc[i, "CODIGO DE PRODUCTO SAP"] for i in mejores]
                    tipo = "ambiguo"

            if not candidatos:
                i = posibles[0]
                sku = df.loc[i, "CODIGO DE PRODUCTO SAP"]
                bodega = df.loc[i, "BODEGA DESDE DONDE SE DESPACHA"]
                if tipo == "sin_match":
                    tipo = "exacto" if desc_n in indice else "contiene"

        enriquecidas.append({
            **f,
            "sku": sku,
            "bodega": bodega,
            "tipo_emparejado": tipo,
            **({"candidatos": candidatos} if candidatos else {})
        })
    return enriquecidas

def imprimir_filas_emparejadas(filas_enriquecidas: list[dict]) -> None:
    if not filas_enriquecidas:
        print("⚠️ No hay filas para imprimir.")
        return
    print(f"{'Uni.':<8} | {'Descripción':<60} | {'Cant':>4} | {'SKU':<10} | {'Bod':>3} | {'Match':<12}")
    print("-" * 112)
    for f in filas_enriquecidas:
        desc = (f.get("desc") or "").strip()
        cant = f.get("cant") or ""
        sku  = f.get("sku") or ""
        bod  = f.get("bodega") or ""
        tip  = f.get("tipo_emparejado") or ""
        print(f"{(f.get('uni') or ''):<8} | {desc[:60]:<60} | {cant:>4} | {sku:<10} | {str(bod):>3} | {tip:<12}")
        if f.get("candidatos"):
            print(f"      ↳ candidatos: {', '.join(f['candidatos'])}")

# ======== CSV opcional para auditoría ========

def guardar_asignaciones_csv(filas_enriquecidas: list[dict], ruta_salida="pedido_asignado.csv"):
    import csv
    columnas = ["uni","desc","cant","puni","ptotal","sku","bodega","tipo_emparejado","candidatos"]
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for r in filas_enriquecidas:
            fila = {k: r.get(k) for k in columnas}
            if isinstance(fila.get("candidatos"), list):
                fila["candidatos"] = " | ".join(fila["candidatos"])
            w.writerow(fila)
    print(f"💾 Guardado CSV: {ruta_salida}")
