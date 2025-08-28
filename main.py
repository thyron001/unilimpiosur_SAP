# main.py
# Servidor Flask + lógica de parseo/matching/persistencia en español
# Integra el escuchador IMAP desde escucha_correos.iniciar_escucha_correos(al_encontrar_pdf)

import os
import io
import re
import pdfplumber
from datetime import datetime
from decimal import Decimal

import psycopg
import pandas as pd
import unicodedata

from threading import Thread
import escucha_correos  # tu módulo de escucha IMAP (en español)

from flask import Flask, render_template, jsonify

app = Flask(__name__)

# =========================
#   PARSEADOR DEL PDF
# =========================

# Palabras típicas de unidad que aparecen en la columna "Unidad" del PDF
PALABRAS_UNIDAD = {
    "Unidad", "RESMA", "Caja", "Rollo", "Paquete",
    "Funda", "Galon", "Kilo", "Par", "Unidad."
}

# Expresiones para detectar filas del cuadro (dos variantes)
PATRON_FILA_CON_UNIDAD = re.compile(
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)
PATRON_FILA_SIN_UNIDAD = re.compile(
    r"^(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

# Líneas a omitir (encabezados, subtotales, bloques de datos de proveedor, etc.)
PALABRAS_OMITIR = (
    "Uni. Descripción", "Subtotal", "TOTAL", "IVA", "Proveedor",
    "ORDEN DE COMPRA", "Fecha:", "Dirección:", "Teléfono:", "Política:",
    "Razón", "RUC:", "E-mail", "Datos de facturación", "Aprueba:",
    "Recibe:", "Analiza:", "Solicita:"
)

def es_linea_omitible(linea: str) -> bool:
    """Devuelve True si la línea es vacía o contiene texto que no es parte de filas de productos."""
    s = (linea or "").strip()
    if not s:
        return True
    return any(palabra in s for palabra in PALABRAS_OMITIR)

def limpiar_unidad(u: str) -> str:
    """Normaliza el texto de unidad eliminando punto final."""
    return (u or "").rstrip(".")

def extraer_filas_pdf(pdf_en_bytes: bytes) -> list[dict]:
    """
    Lee el PDF (bytes) y devuelve una lista de filas:
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

                # Caso A: la línea es solo la unidad (p.ej. "Paquete", "Unidad")
                if linea in PALABRAS_UNIDAD:
                    unidad_en_espera = limpiar_unidad(linea)
                    continue

                # Caso B: la fila trae unidad al inicio
                m = PATRON_FILA_CON_UNIDAD.match(linea)
                if m and limpiar_unidad(m.group("uni")) in PALABRAS_UNIDAD:
                    d = m.groupdict()
                    d["uni"] = limpiar_unidad(d["uni"])
                    filas.append(d)
                    unidad_en_espera = None
                    continue

                # Caso C: la unidad vino en la línea anterior
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
    """Imprime en consola las filas crudas detectadas del PDF (para diagnóstico)."""
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

# =========================
#   CATÁLOGO & EMPAREJADO
# =========================

RUTA_CATALOGO = os.getenv("PRODUCT_CSV", "productos_roldan.csv")
CATALOGO_CACHE: pd.DataFrame | None = None

def normalizar_texto(s: str) -> str:
    """Mayúsculas, sin tildes, solo [A-Z0-9 espacio], espacios colapsados."""
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def solapamiento_tokens(a: str, b: str) -> int:
    """Cuenta cuántos tokens (>=3 chars) de 'a' aparecen en 'b'."""
    toks = [t for t in a.split() if len(t) >= 3]
    bset = set(b.split())
    return sum(1 for t in toks if t in bset)

def cargar_catalogo(ruta: str = RUTA_CATALOGO) -> pd.DataFrame:
    """Carga el catálogo (con cache en memoria) y agrega columnas normalizadas."""
    global CATALOGO_CACHE
    if CATALOGO_CACHE is not None:
        return CATALOGO_CACHE
    df = pd.read_csv(ruta, dtype=str)
    columnas_requeridas = [
        "Unidad",
        "NOMBRE DE ARTICULO EN LA ORDEN",
        "CODIGO DE PRODUCTO SAP",
        "BODEGA DESDE DONDE SE DESPACHA",
    ]
    for c in columnas_requeridas:
        if c not in df.columns:
            raise RuntimeError(f"CSV de catálogo no tiene la columna requerida: {c}")
    df["nombre_norm"]  = df["NOMBRE DE ARTICULO EN LA ORDEN"].map(normalizar_texto)
    df["unidad_norm"]  = df["Unidad"].map(normalizar_texto)
    CATALOGO_CACHE = df
    return CATALOGO_CACHE

def construir_indice_nombres(df: pd.DataFrame) -> dict[str, list[int]]:
    """Devuelve un índice nombre_norm -> [índices en df]."""
    idx: dict[str, list[int]] = {}
    for i, s in enumerate(df["nombre_norm"]):
        idx.setdefault(s, []).append(i)
    return idx

def emparejar_filas_con_catalogo(filas: list[dict], ruta_csv: str = RUTA_CATALOGO) -> list[dict]:
    """
    Devuelve filas enriquecidas con:
      - 'sku' (CODIGO DE PRODUCTO SAP)
      - 'bodega' (BODEGA DESDE DONDE SE DESPACHA)
      - 'tipo_emparejado' en {'exacto','contiene','contiene+unidad','ambiguo','sin_match'}
      - 'candidatos' (opcional) lista de SKUs cuando quedó ambiguo
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
    """Imprime filas ya enriquecidas con SKU/Bodega/Tipo de match."""
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

# =========================
#   UTILIDADES DE PERSISTENCIA
# =========================

def guardar_asignaciones_csv(filas_enriquecidas: list[dict], ruta_salida="pedido_asignado.csv"):
    """Guarda un CSV con las asignaciones (para auditoría)."""
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

def a_decimal(valor) -> Decimal | None:
    """Convierte '12,50' o '12.50' a Decimal; None si no aplica."""
    if valor is None:
        return None
    s = str(valor).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

def obtener_conexion_pg():
    """Crea conexión a PostgreSQL usando PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE del entorno."""
    return psycopg.connect()

def guardar_pedido_en_pg(filas_enriquecidas: list[dict], meta: dict):
    """
    Inserta en PostgreSQL:
      - pedidos(fecha, total, pdf_filename, email_uid, email_from, email_subject)
      - pedido_items(pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)
    """
    if not filas_enriquecidas:
        print("⚠️ No hay filas enriquecidas para guardar en PostgreSQL.")
        return

    # Total del pedido (si el PDF no trae total explícito)
    total = Decimal("0")
    for f in filas_enriquecidas:
        pt = a_decimal(f.get("ptotal"))
        if pt is not None:
            total += pt

    # Fecha preferida: la del correo (ENVELOPE), si no existe usa ahora()
    fecha = meta.get("fecha")
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except Exception:
            fecha = datetime.now()
    elif not isinstance(fecha, datetime):
        fecha = datetime.now()

    pdf_filename  = meta.get("pdf_filename")
    email_uid     = meta.get("email_uid")
    email_from    = meta.get("email_from")
    email_subject = meta.get("email_subject")

    with obtener_conexion_pg() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pedidos (fecha, total, pdf_filename, email_uid, email_from, email_subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, numero_pedido;
                """,
                (fecha, total, pdf_filename, email_uid, email_from, email_subject)
            )
            pedido_id, numero_pedido = cur.fetchone()

            for f in filas_enriquecidas:
                cur.execute(
                    """
                    INSERT INTO pedido_items
                    (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        pedido_id,
                        (f.get("desc") or "").strip(),
                        f.get("sku"),
                        f.get("bodega"),
                        int(f.get("cant") or 0),
                        a_decimal(f.get("puni")),
                        a_decimal(f.get("ptotal")),
                    )
                )
    print(f"✅ Pedido guardado en PostgreSQL. ID={pedido_id} | N° orden llegada={numero_pedido} | Ítems={len(filas_enriquecidas)}")

# =========================
#   CALLBACK DEL ESCUCHADOR
# =========================

def al_encontrar_pdf(meta: dict, nombre_pdf: str, pdf_en_bytes: bytes) -> None:
    """
    Callback invocado por escucha_correos.iniciar_escucha_correos cuando llega un correo con PDF.
    meta: { uid:int, fecha:datetime|None, asunto:str, remitente:str }
    """
    print("\n=== 📬 Nuevo correo (callback) ===")
    print(f"De:      {meta.get('remitente','')}")
    print(f"Asunto:  {meta.get('asunto','')}")
    print(f"Fecha:   {meta.get('fecha')}")
    print(f"UID:     {meta.get('uid')}")
    print(f"📎 PDF:  {nombre_pdf}")

    filas = extraer_filas_pdf(pdf_en_bytes)
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return

    filas_enriquecidas = emparejar_filas_con_catalogo(filas, RUTA_CATALOGO)
    imprimir_filas_emparejadas(filas_enriquecidas)
    guardar_asignaciones_csv(filas_enriquecidas)

    meta_pedido = {
        "fecha": meta.get("fecha"),
        "pdf_filename": nombre_pdf,
        "email_uid": int(meta.get("uid") or 0),
        "email_from": meta.get("remitente"),
        "email_subject": meta.get("asunto"),
    }
    guardar_pedido_en_pg(filas_enriquecidas, meta_pedido)

# =========================
#   RUTAS FLASK
# =========================

@app.route("/pedidos")
def ver_pedidos():
    """HTML con la tabla de pedidos (últimos 200)."""
    with obtener_conexion_pg() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT numero_pedido, fecha, total
            FROM pedidos
            ORDER BY id DESC
            LIMIT 200;
        """)
        filas = [{"numero_pedido": n, "fecha": f, "total": t}
                 for (n, f, t) in cur.fetchall()]
    return render_template("orders.html", orders=filas, now=datetime.utcnow())

@app.route("/api/orders/summary")
def resumen_pedidos():
    """API mínima para avisar cantidad de pedidos (para indicador de nuevos)."""
    with obtener_conexion_pg() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos;")
        (cantidad,) = cur.fetchone()
    return jsonify({"count": int(cantidad)})

# =========================
#   ARRANQUE
# =========================

if __name__ == "__main__":
    # Evita lanzar dos hilos con el reloader en modo debug
    es_proceso_principal = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)
    if es_proceso_principal:
        hilo_imap = Thread(
            target=escucha_correos.iniciar_escucha_correos,
            args=(al_encontrar_pdf,),
            name="hilo-escucha-imap",
            daemon=True
        )
        hilo_imap.start()
        print("🧵 Hilo IMAP iniciado.")

    app.run(host="0.0.0.0", port=5000, debug=True)
