import os
import ssl
import time
import io
import re
import pdfplumber
from email import message_from_bytes
from email.header import decode_header, make_header
from imapclient import IMAPClient

from datetime import datetime
from decimal import Decimal
import psycopg


from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# =========================
#   CATALOGO & MATCHING
# =========================
import unicodedata
import pandas as pd

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
MAILBOX   = os.getenv("IMAP_MAILBOX", "INBOX")
IDLE_SECS = int(os.getenv("IMAP_IDLE_SECS", "1740"))  # ~29 min

# =========================
#   PARSER DEL PDF (tuyo)
# =========================
# Palabras de unidad que aparecen en el PDF (puedes agregar más si hiciera falta)
UNIT_WORDS = {
    "Unidad", "RESMA", "Caja", "Rollo", "Paquete",
    "Funda", "Galon", "Kilo", "Par", "Unidad."
}

# Filas con "unidad + descripción + cant + p.uni + p.total" en UNA MISMA LÍNEA
LINE_W_UNIT = re.compile(
    r"^(?P<uni>\S+)\s+(?P<desc>.+?)\s+(?P<cant>\d{1,4})\s+(?P<puni>\d+(?:[.,]\d+)?)\s+(?P<ptotal>\d+(?:[.,]\d+)?)$"
)

# Filas donde la UNIDAD VIENE EN LÍNEA ANTERIOR -> aquí solo hay "desc + cant + p.uni + p.total"
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
    """
    Procesa el PDF (bytes) y devuelve una lista de filas con:
    { 'uni': str, 'desc': str, 'cant': str, 'puni': str, 'ptotal': str }
    """
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        pending_unit = None  # si una línea es solo "Paquete", "Unidad", etc., se guarda aquí
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for raw in text.splitlines():
                line = raw.strip()
                if should_skip(line):
                    continue

                # ¿La línea es SOLO la unidad?
                if line in UNIT_WORDS:
                    pending_unit = clean_unit(line)
                    continue

                # Intento 1: toda la fila viene en la misma línea (con unidad al inicio)
                m = LINE_W_UNIT.match(line)
                if m and clean_unit(m.group("uni")) in UNIT_WORDS:
                    d = m.groupdict()
                    d["uni"] = clean_unit(d["uni"])
                    rows.append(d)
                    pending_unit = None
                    continue

                # Intento 2: la unidad venía en la línea anterior; esta línea trae desc + números
                if pending_unit:
                    m2 = LINE_WO_UNIT.match(line)
                    if m2:
                        d = m2.groupdict()
                        d["uni"] = pending_unit
                        rows.append(d)
                        pending_unit = None
                        continue

                # Si no encaja, la ignoramos (encabezados raros, saltos, etc.)
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
    """Normaliza: mayúsculas, sin tildes, solo [A-Z0-9 espacio], colapsa espacios."""
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _token_overlap(a: str, b: str) -> int:
    """Cantidad de tokens (>=3 caracteres) de a que están en b."""
    toks = [t for t in a.split() if len(t) >= 3]
    bset = set(b.split())
    return sum(1 for t in toks if t in bset)

def _load_catalog(path: str = CATALOG_PATH) -> pd.DataFrame:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    df = pd.read_csv(path, dtype=str)
    # Columnas esperadas:
    #  - "NOMBRE DE ARTICULO EN LA ORDEN" (nombre)
    #  - "CODIGO DE PRODUCTO SAP" (SKU)
    #  - "BODEGA DESDE DONDE SE DESPACHA" (bodega)
    #  - "Unidad" (puede venir vacío; cuando exista, ayuda a desambiguar)
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
    """
    Devuelve nuevas filas con claves adicionales:
      - sku
      - bodega
      - match_type: 'exact', 'contains', 'contains+unit', 'ambiguous', 'unmatched'
      - candidates: lista (opcional) de SKUs candidatos cuando quede ambiguo
    """
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

        # 1) Exacto
        if desc_n in name_index:
            cand_idx = name_index[desc_n]
        else:
            # 2) Contención (PDF en catálogo o catálogo en PDF)
            cand_idx = [
                i for i, nm in enumerate(df["name_norm"])
                if desc_n and (desc_n in nm or nm in desc_n)
            ]

        # 3) Si hay candidatos, intentamos afinar por unidad
        if cand_idx:
            # Si hay muchos, primero probamos por unidad exacta (cuando el catálogo la tenga)
            if unit_n:
                by_unit = [i for i in cand_idx if df.loc[i, "unidad_norm"] == unit_n]
                if by_unit:
                    cand_idx = by_unit
                    match_type = "contains+unit" if match_type != "exact" else "exact"
                else:
                    # Si la unidad no figura en 'Unidad', intentamos si aparece como texto en el nombre
                    by_name_unit = [i for i in cand_idx if unit_n and unit_n in df.loc[i, "name_norm"]]
                    if by_name_unit:
                        cand_idx = by_name_unit
                        match_type = "contains+unit"

            # Si siguen quedando varios, desempatar por mayor solapamiento de tokens
            if len(cand_idx) > 1:
                overlaps = [(i, _token_overlap(desc_n, df.loc[i, "name_norm"])) for i in cand_idx]
                max_ol = max(o for _, o in overlaps)
                best = [i for i, o in overlaps if o == max_ol]
                if len(best) == 1:
                    cand_idx = best
                else:
                    # Aún ambiguo: devolvemos candidatos
                    candidates = [df.loc[i, "CODIGO DE PRODUCTO SAP"] for i in best]
                    match_type = "ambiguous"

            if not candidates:
                # Candidato definitivo
                i = cand_idx[0]
                sku = df.loc[i, "CODIGO DE PRODUCTO SAP"]
                bodega = df.loc[i, "BODEGA DESDE DONDE SE DESPACHA"]
                if match_type == "unmatched":
                    # si llegamos aquí sin poner el tipo, es exacto o contains sin unidad
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
#   IMAP + DETECCIÓN PDF
# =========================

# Variable global para almacenar el último PDF detectado y sus filas parseadas
LAST_PDF = {"bytes": None, "filename": None, "uid": None, "rows": None}

def decode_maybe(value):
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)

def _safe_decode_filename(fname):
    if not fname:
        return ""
    try:
        return str(make_header(decode_header(fname)))
    except Exception:
        return fname

def _extract_first_pdf_from_message(raw_bytes):
    """
    Dado el mensaje crudo (RFC822), devuelve (pdf_filename, pdf_bytes) del primer PDF encontrado,
    o (None, None) si no hay PDF adjuntos.
    """
    msg = message_from_bytes(raw_bytes)
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        ctype = (part.get_content_type() or "").lower()
        fname = _safe_decode_filename(part.get_filename())
        is_pdf_by_type = ctype == "application/pdf"
        is_pdf_by_name = fname.lower().endswith(".pdf") if fname else False
        if is_pdf_by_type or is_pdf_by_name:
            try:
                payload = part.get_payload(decode=True)
            except Exception:
                payload = None
            if payload:
                if not fname:
                    fname = "adjunto.pdf"
                return fname, payload
    return None, None

def fetch_and_print_new(client, since_uid):
    # Busca no leídos y filtra por UID para evitar duplicados
    new_uids = [uid for uid in client.search(["UNSEEN"]) if uid > since_uid]
    if not new_uids:
        return since_uid

    response_env = client.fetch(new_uids, ["ENVELOPE"])

    for uid in sorted(new_uids):
        env = response_env[uid].get(b"ENVELOPE")
        if not env:
            continue

        subject = decode_maybe(env.subject.decode() if isinstance(env.subject, bytes) else env.subject)
        from_addr = ""
        if env.from_:
            frm = env.from_[0]
            name = (frm.name or b"").decode(errors="ignore") if isinstance(frm.name, bytes) else (frm.name or "")
            mailbox = (frm.mailbox or b"").decode(errors="ignore")
            host = (frm.host or b"").decode(errors="ignore")
            pretty_name = decode_maybe(name).strip()
            email_addr = f"{mailbox}@{host}" if mailbox and host else ""
            from_addr = (f"{pretty_name} <{email_addr}>" if pretty_name else email_addr) or "(desconocido)"
        date_str = env.date.strftime("%Y-%m-%d %H:%M:%S") if env.date else ""

        # Leer mensaje completo para buscar PDF
        resp_full = client.fetch([uid], ["RFC822"])
        raw_bytes = resp_full[uid].get(b"RFC822", b"")
        pdf_name, pdf_bytes = _extract_first_pdf_from_message(raw_bytes)

        print("\n=== 📬 Nuevo correo ===")
        print(f"De:      {from_addr}")
        print(f"Asunto:  {subject}")
        print(f"Fecha:   {date_str}")
        print(f"UID:     {uid}")

        if pdf_bytes:
            LAST_PDF["bytes"] = pdf_bytes
            LAST_PDF["filename"] = pdf_name
            LAST_PDF["uid"] = uid
            print(f"📎 PDF detectado: SÍ  -> '{pdf_name}' (guardado en memoria)")

            # === Procesar PDF inmediatamente ===
            try:
                rows = process_pdf_bytes(pdf_bytes)
                LAST_PDF["rows"] = rows
                if rows:
                    print("\n🧾 Filas extraídas del PDF:")
                    # Enriquecer con SKU y bodega desde el CSV
                    rows_enriched = match_rows_with_catalog(rows, CATALOG_PATH)
                    print_rows_with_match(rows_enriched)
                    # 💾 Guardar a CSV
                    save_assignments_csv(rows_enriched)
                    
                    
                    # 💾💾 NUEVO: Guardar en PostgreSQL
                    order_meta = {
                        # Usa la fecha del ENVELOPE si está; si no, la función pondrá now()
                        "fecha": env.date if env and getattr(env, "date", None) else None,
                        "pdf_filename": pdf_name,
                        "email_uid": int(uid),
                        "email_from": from_addr,
                        "email_subject": subject,
                    }
                    persist_order_to_pg(rows_enriched, order_meta)
                    
            except Exception as e:
                print(f"⚠️  Error al procesar el PDF: {e}")
        else:
            print("📎 PDF detectado: NO")
            

    return max(since_uid, max(new_uids))

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
    # Cambia coma por punto (e.g., "12,50" -> "12.50")
    s = s.replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return None

def get_pg_conn():
    # Usa las variables de entorno que ya configuraste (PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
    return psycopg.connect()


def persist_order_to_pg(rows_enriched: list[dict], meta: dict):
    """
    Inserta en PostgreSQL:
      - pedidos(id, numero_pedido [DEFAULT], fecha, total, pdf_filename, email_uid, email_from, email_subject)
      - pedido_items(...)
    'meta' debe traer: fecha(datetime), pdf_filename, email_uid, email_from, email_subject
    """
    if not rows_enriched:
        print("⚠️ No hay filas enriquecidas para guardar en PostgreSQL.")
        return

    # Calcular total = suma de ptotal de ítems (si no tienes un 'TOTAL' del PDF)
    total = Decimal("0")
    for r in rows_enriched:
        pt = to_decimal(r.get("ptotal"))
        if pt is not None:
            total += pt

    # Fecha del pedido (desde el correo si la tenemos)
    fecha = meta.get("fecha")
    if isinstance(fecha, str):
        # Intento parsear por si llega string
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

    # Insertar en BD
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            # Insert pedido (numero_pedido se autogenera por DEFAULT con la secuencia)
            cur.execute(
                """
                INSERT INTO pedidos (fecha, total, pdf_filename, email_uid, email_from, email_subject)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, numero_pedido;
                """,
                (fecha, total, pdf_filename, email_uid, email_from, email_subject)
            )
            pedido_id, numero_pedido = cur.fetchone()

            # Insert items
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
        # with conn: hace commit automáticamente si no hay excepción

    print(f"✅ Pedido guardado en PostgreSQL. ID={pedido_id}  | N° orden llegada={numero_pedido}  | Ítems={len(rows_enriched)}")




def imap_loop():
    if not IMAP_USER or not IMAP_PASS:
        raise SystemExit("Faltan variables de entorno IMAP_USER y/o IMAP_PASS.")

    context = ssl.create_default_context()
    print(f"Conectando a {IMAP_HOST} como {IMAP_USER} ...")

    while True:
        try:
            with IMAPClient(IMAP_HOST, ssl=True, ssl_context=context, timeout=60) as client:
                client.login(IMAP_USER, IMAP_PASS)
                client.select_folder(MAILBOX)
                print(f"Conectado. Escuchando nuevos correos en '{MAILBOX}' (IDLE). Ctrl+C para salir.")

                status = client.folder_status(MAILBOX, [b"UIDNEXT"])
                last_seen_uid = (status.get(b"UIDNEXT") or 1) - 1

                while True:
                    last_seen_uid = fetch_and_print_new(client, last_seen_uid)
                    client.idle()
                    try:
                        responses = client.idle_check(timeout=IDLE_SECS)
                    finally:
                        try:
                            client.idle_done()
                        except Exception:
                            pass
                    if responses:
                        last_seen_uid = fetch_and_print_new(client, last_seen_uid)

        except KeyboardInterrupt:
            print("\nSaliendo…")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}. Reintentando en 10s…")
            time.sleep(10)

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


from threading import Thread
            
if __name__ == "__main__":
    # Evita lanzar dos hilos con el reloader de Flask
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        t = Thread(target=imap_loop, name="imap-listener", daemon=True)
        t.start()
        print("🧵 Hilo IMAP iniciado.")

    app.run(host="0.0.0.0", port=5000, debug=True)
