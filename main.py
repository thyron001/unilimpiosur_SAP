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
import escucha_correos

from flask import Flask, render_template

app = Flask(__name__)

# =========================
#   PARSER DEL PDF (tuyo)
# =========================
UNIT_WORDS = {
    "Unidad", "RESMA", "Caja", "Rollo", "Paquete",
    "Funda", "Galon", "Kilo", "Par", "Unidad."
}

LINE_W_UNIT = re.compile(
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)
LINE_WO_UNIT = re.compile(
    r"^(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

SKIP_IF_CONTAINS = (
    "Uni. Descripción", "Subtotal", "TOTAL", "IVA", "Proveedor",
    "ORDEN DE COMPRA", "Fecha:", "Dirección:", "Teléfono:", "Política:",
    "Razón", "RUC:", "E-mail", "Datos de facturación", "Aprueba:", "Recibe:", "Analiza:", "Solicita:"
)

def should_skip(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    for kw in SKIP_IF_CONTAINS:
        if kw in s:
            return True
    return False

def clean_unit(u: str) -> str:
    return u.rstrip(".")

def process_pdf_bytes(pdf_bytes: bytes) -> list[dict]:
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pending_unit = None
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for raw in text.splitlines():
                line = raw.strip()
                if should_skip(line):
                    continue

                if line in UNIT_WORDS:
                    pending_unit = clean_unit(line)
                    continue

                m = LINE_W_UNIT.match(line)
                if m and clean_unit(m.group("uni")) in UNIT_WORDS:
                    d = m.groupdict()
                    d["uni"] = clean_unit(d["uni"])
                    rows.append(d)
                    pending_unit = None
                    continue

                if pending_unit:
                    m2 = LINE_WO_UNIT.match(line)
                    if m2:
                        d = m2.groupdict()
                        d["uni"] = pending_unit
                        rows.append(d)
                        pending_unit = None
                        continue
    return rows

def print_rows(rows: list[dict]) -> None:
    if not rows:
        print("⚠️ No se detectaron filas en el PDF.")
        return
    print(f"{'Uni.':<10} | {'Descripción':<70} | {'Cant':>4} | {'P. Uni':>8} | {'P. Total':>9}")
    print("-" * 110)
    for r in rows:
        desc = r["desc"].strip()
        cant = r["cant"]
        puni = r["puni"].replace(",", ".")
        ptotal = r["ptotal"].replace(",", ".")
        uni = r["uni"]
        print(f"{uni:<10} | {desc[:70]:<70} | {cant:>4} | {puni:>8} | {ptotal:>9}")

# =========================
#   CATALOGO & MATCHING
# =========================
CATALOG_PATH = os.getenv("PRODUCT_CSV", "productos_roldan.csv")
_CATALOG = None

def _norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _token_overlap(a: str, b: str) -> int:
    toks = [t for t in a.split() if len(t) >= 3]
    bset = set(b.split())
    return sum(1 for t in toks if t in bset)

def _load_catalog(path: str = CATALOG_PATH) -> pd.DataFrame:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    df = pd.read_csv(path, dtype=str)
    for c in ["Unidad", "NOMBRE DE ARTICULO EN LA ORDEN", "CODIGO DE PRODUCTO SAP", "BODEGA DESDE DONDE SE DESPACHA"]:
        if c not in df.columns:
            raise RuntimeError(f"CSV de catálogo no tiene la columna requerida: {c}")
    df["name_norm"]   = df["NOMBRE DE ARTICULO EN LA ORDEN"].map(_norm_text)
    df["unidad_norm"] = df["Unidad"].map(_norm_text)
    _CATALOG = df
    return _CATALOG

def _build_name_index(df: pd.DataFrame) -> dict[str, list[int]]:
    idx = {}
    for i, s in enumerate(df["name_norm"]):
        idx.setdefault(s, []).append(i)
    return idx

def match_rows_with_catalog(rows: list[dict], csv_path: str = CATALOG_PATH) -> list[dict]:
    df = _load_catalog(csv_path)
    name_index = _build_name_index(df)

    enriched = []
    for r in rows:
        desc_raw = r.get("desc", "")
        unit_raw = r.get("uni", "")
        desc_n   = _norm_text(desc_raw)
        unit_n   = _norm_text(unit_raw)

        sku = None
        bodega = None
        match_type = "unmatched"
        candidates = []

        if desc_n in name_index:
            cand_idx = name_index[desc_n]
        else:
            cand_idx = [
                i for i, nm in enumerate(df["name_norm"])
                if desc_n and (desc_n in nm or nm in desc_n)
            ]

        if cand_idx:
            if unit_n:
                by_unit = [i for i in cand_idx if df.loc[i, "unidad_norm"] == unit_n]
                if by_unit:
                    cand_idx = by_unit
                    match_type = "contains+unit" if match_type != "exact" else "exact"
                else:
                    by_name_unit = [i for i in cand_idx if unit_n and unit_n in df.loc[i, "name_norm"]]
                    if by_name_unit:
                        cand_idx = by_name_unit
                        match_type = "contains+unit"

            if len(cand_idx) > 1:
                overlaps = [(i, _token_overlap(desc_n, df.loc[i, "name_norm"])) for i in cand_idx]
                max_ol = max(o for _, o in overlaps)
                best = [i for i, o in overlaps if o == max_ol]
                if len(best) == 1:
                    cand_idx = best
                else:
                    candidates = [df.loc[i, "CODIGO DE PRODUCTO SAP"] for i in best]
                    match_type = "ambiguous"

            if not candidates:
                i = cand_idx[0]
                sku = df.loc[i, "CODIGO DE PRODUCTO SAP"]
                bodega = df.loc[i, "BODEGA DESDE DONDE SE DESPACHA"]
                if match_type == "unmatched":
                    match_type = "exact" if desc_n in name_index else "contains"

        enriched.append({
            **r,
            "sku": sku,
            "bodega": bodega,
            "match_type": match_type,
            **({"candidates": candidates} if candidates else {})
        })
    return enriched

def print_rows_with_match(rows_enriched: list[dict]) -> None:
    if not rows_enriched:
        print("⚠️ No hay filas para imprimir.")
        return
    print(f"{'Uni.':<8} | {'Descripción':<60} | {'Cant':>4} | {'SKU':<10} | {'Bod':>3} | {'Tipo':<10}")
    print("-" * 110)
    for r in rows_enriched:
        desc   = (r.get("desc") or "").strip()
        cant   = r.get("cant") or ""
        sku    = r.get("sku") or ""
        bodeg  = (r.get("bodega") or "")
        mtype  = r.get("match_type") or ""
        print(f"{(r.get('uni') or ''):<8} | {desc[:60]:<60} | {cant:>4} | {sku:<10} | {str(bodeg):>3} | {mtype:<10}")
        if r.get("candidates"):
            print(f"      ↳ candidatos: {', '.join(r['candidates'])}")

# =========================
#   UTILIDADES PERSISTENCIA
# =========================
def save_assignments_csv(rows_enriched: list[dict], out_path="pedido_asignado.csv"):
    import csv
    cols = ["uni","desc","cant","puni","ptotal","sku","bodega","match_type","candidates"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows_enriched:
            row = {k: r.get(k) for k in cols}
            if isinstance(row.get("candidates"), list):
                row["candidates"] = " | ".join(row["candidates"])
            w.writerow(row)
    print(f"💾 Guardado: {out_path}")

def to_decimal(s) -> Decimal | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

def get_pg_conn():
    return psycopg.connect()

def persist_order_to_pg(rows_enriched: list[dict], meta: dict):
    if not rows_enriched:
        print("⚠️ No hay filas enriquecidas para guardar en PostgreSQL.")
        return

    total = Decimal("0")
    for r in rows_enriched:
        pt = to_decimal(r.get("ptotal"))
        if pt is not None:
            total += pt

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

    with get_pg_conn() as conn:
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

            for r in rows_enriched:
                cur.execute(
                    """
                    INSERT INTO pedido_items
                    (pedido_id, descripcion, sku, bodega, cantidad, precio_unitario, precio_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        pedido_id,
                        (r.get("desc") or "").strip(),
                        r.get("sku"),
                        r.get("bodega"),
                        int(r.get("cant") or 0),
                        to_decimal(r.get("puni")),
                        to_decimal(r.get("ptotal")),
                    )
                )
    print(f"✅ Pedido guardado en PostgreSQL. ID={pedido_id}  | N° orden llegada={numero_pedido}  | Ítems={len(rows_enriched)}")

# =========================
#   CALLBACK PARA ESCUCHA
# =========================
def al_encontrar_pdf(meta: dict, nombre_pdf: str, bytes_pdf: bytes) -> None:
    print("\n=== 📬 Nuevo correo (callback) ===")
    print(f"De:      {meta.get('remitente','')}")
    print(f"Asunto:  {meta.get('asunto','')}")
    print(f"Fecha:   {meta.get('fecha')}")
    print(f"UID:     {meta.get('uid')}")
    print(f"📎 PDF:  {nombre_pdf}")

    filas = process_pdf_bytes(bytes_pdf)
    if not filas:
        print("⚠️ No se detectaron filas en el PDF.")
        return

    filas_enriquecidas = match_rows_with_catalog(filas, CATALOG_PATH)
    print_rows_with_match(filas_enriquecidas)
    save_assignments_csv(filas_enriquecidas)

    meta_pedido = {
        "fecha": meta.get("fecha"),
        "pdf_filename": nombre_pdf,
        "email_uid": int(meta.get("uid") or 0),
        "email_from": meta.get("remitente"),
        "email_subject": meta.get("asunto"),
    }
    persist_order_to_pg(filas_enriquecidas, meta_pedido)

# =========================
#   RUTAS FLASK
# =========================
@app.route("/pedidos")
def pedidos():
    with get_pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT numero_pedido, fecha, total FROM pedidos ORDER BY id DESC LIMIT 200;")
        rows = [
            {"numero_pedido": n, "fecha": f, "total": t}
            for (n, f, t) in cur.fetchall()
        ]
    return render_template("orders.html", orders=rows, now=datetime.utcnow())

@app.route("/api/orders/summary")
def orders_summary():
    with get_pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pedidos;")
        (count,) = cur.fetchone()
    return {"count": int(count)}

# =========================
#   ARRANQUE
# =========================
if __name__ == "__main__":
    es_proceso_principal = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or (not app.debug)
    if es_proceso_principal:
        t = Thread(
            target=escucha_correos.iniciar_escucha_correos,
            args=(al_encontrar_pdf,),
            name="hilo-escucha-imap",
            daemon=True
        )
        t.start()
        print("🧵 Hilo IMAP iniciado.")

    app.run(host="0.0.0.0", port=5000, debug=True)
