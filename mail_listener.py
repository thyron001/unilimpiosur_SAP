# mail_listener.py
# Módulo de escucha IMAP que detecta el PRIMER PDF de cada correo nuevo
# y llama a un callback con los metadatos + bytes del PDF.

import os
import ssl
import time
from typing import Callable, Dict, Any, Tuple
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header

# --- Config (desde variables de entorno) ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
MAILBOX   = os.getenv("IMAP_MAILBOX", "INBOX")
IDLE_SECS = int(os.getenv("IMAP_IDLE_SECS", "1740"))  # 29 min por defecto

# ---------- Helpers de decodificación ----------
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

def _extract_first_pdf_from_message(raw_bytes: bytes) -> Tuple[str | None, bytes | None]:
    """
    Devuelve (pdf_filename, pdf_bytes) del primer PDF encontrado, o (None, None).
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

# ---------- Núcleo del listener ----------
def _pull_new(client: IMAPClient, since_uid: int, on_pdf: Callable[[Dict[str, Any], str, bytes], None]) -> int:
    """
    Revisa correos UNSEEN con UID > since_uid. Si hay PDF, llama on_pdf(meta, filename, pdf_bytes).
    Retorna el nuevo since_uid.
    """
    new_uids = [uid for uid in client.search(["UNSEEN"]) if uid > since_uid]
    if not new_uids:
        return since_uid

    # Pedimos ENVELOPE y RFC822 para todos los nuevos
    response = client.fetch(new_uids, ["ENVELOPE", "RFC822"])

    for uid in sorted(new_uids):
        env = response[uid].get(b"ENVELOPE")
        raw_bytes = response[uid].get(b"RFC822", b"")
        if not env:
            continue

        # Decodificar metadatos mínimos (ya listos para usar)
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

        pdf_name, pdf_bytes = _extract_first_pdf_from_message(raw_bytes)

        # Meta simplificado para el callback
        meta = {
            "uid": int(uid),
            "date": env.date,          # datetime | None
            "subject": subject,        # str
            "from_addr": from_addr,    # str
        }

        if pdf_bytes:
            try:
                on_pdf(meta, pdf_name or "adjunto.pdf", pdf_bytes)
            except Exception as cb_err:
                print(f"⚠️  Error en callback on_pdf: {cb_err}")

    return max(since_uid, max(new_uids))

def run_imap_listener(on_pdf: Callable[[Dict[str, Any], str, bytes], None]) -> None:
    """
    Bucle infinito que mantiene la sesión IMAP viva y llama al callback cuando llegue un PDF.
    """
    if not IMAP_USER or not IMAP_PASS:
        print("❌ Faltan IMAP_USER/IMAP_PASS en variables de entorno. Listener no iniciado.")
        return

    context = ssl.create_default_context()
    print(f"Conectando a {IMAP_HOST} como {IMAP_USER} ...")

    while True:
        try:
            with IMAPClient(IMAP_HOST, ssl=True, ssl_context=context, timeout=60) as client:
                client.login(IMAP_USER, IMAP_PASS)
                client.select_folder(MAILBOX)
                print(f"Conectado. Escuchando nuevos correos en '{MAILBOX}' (IDLE).")

                status = client.folder_status(MAILBOX, [b"UIDNEXT"])
                last_seen_uid = (status.get(b"UIDNEXT") or 1) - 1

                while True:
                    last_seen_uid = _pull_new(client, last_seen_uid, on_pdf)
                    client.idle()
                    try:
                        responses = client.idle_check(timeout=IDLE_SECS)
                    finally:
                        try:
                            client.idle_done()
                        except Exception:
                            pass
                    if responses:
                        last_seen_uid = _pull_new(client, last_seen_uid, on_pdf)

        except KeyboardInterrupt:
            print("\nSaliendo del listener IMAP…")
            break
        except Exception as e:
            print(f"⚠️  IMAP listener error: {e}. Reintentando en 10s…")
            time.sleep(10)
