import os
import ssl
import time
from email import message_from_bytes
from email.header import decode_header, make_header
from imapclient import IMAPClient

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
MAILBOX   = os.getenv("IMAP_MAILBOX", "INBOX")
IDLE_SECS = int(os.getenv("IMAP_IDLE_SECS", "1740"))  # ~29 min

# Variable global para almacenar el último PDF detectado
# LAST_PDF["bytes"] -> contenido en bytes
# LAST_PDF["filename"] -> nombre del archivo
# LAST_PDF["uid"] -> UID del correo del cual se extrajo
LAST_PDF = {"bytes": None, "filename": None, "uid": None}

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
        # Soporta nombres codificados RFC2231/2047
        return str(make_header(decode_header(fname)))
    except Exception:
        return fname

def _extract_first_pdf_from_message(raw_bytes):
    """
    Dado el mensaje crudo (RFC822), devuelve (pdf_filename, pdf_bytes) del primer PDF encontrado,
    o (None, None) si no hay PDF adjuntos.
    """
    msg = message_from_bytes(raw_bytes)

    # Recorremos todas las partes del mensaje
    for part in msg.walk():
        # Saltar contenedores
        if part.get_content_maintype() == "multipart":
            continue

        ctype = (part.get_content_type() or "").lower()
        fname = _safe_decode_filename(part.get_filename())

        is_pdf_by_type = ctype == "application/pdf"
        is_pdf_by_name = fname.lower().endswith(".pdf") if fname else False

        if is_pdf_by_type or is_pdf_by_name:
            try:
                payload = part.get_payload(decode=True)  # bytes
            except Exception:
                payload = None

            if payload:
                if not fname:
                    # Nombre genérico si viene sin filename
                    fname = "adjunto.pdf"
                return fname, payload

    return None, None

def fetch_and_print_new(client, since_uid):
    # Busca no leídos y filtra por UID para evitar duplicados
    new_uids = [uid for uid in client.search(["UNSEEN"]) if uid > since_uid]
    if not new_uids:
        return since_uid

    # Traemos ENVELOPE para cabeceras y luego el RFC822 para examinar adjuntos
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

        # Ahora leemos el mensaje completo para buscar PDFs
        resp_full = client.fetch([uid], ["RFC822"])
        raw_bytes = resp_full[uid].get(b"RFC822", b"")
        pdf_name, pdf_bytes = _extract_first_pdf_from_message(raw_bytes)

        # Mostrar información en terminal
        print("\n=== 📬 Nuevo correo ===")
        print(f"De:      {from_addr}")
        print(f"Asunto:  {subject}")
        print(f"Fecha:   {date_str}")
        print(f"UID:     {uid}")

        if pdf_bytes:
            # Guardamos en variable global
            LAST_PDF["bytes"] = pdf_bytes
            LAST_PDF["filename"] = pdf_name
            LAST_PDF["uid"] = uid
            print(f"📎 PDF detectado: SÍ  -> '{pdf_name}' (guardado en variable LAST_PDF)")
        else:
            print("📎 PDF detectado: NO")

    return max(since_uid, max(new_uids))

def main():
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
                    # por si llegaron entre ciclos
                    last_seen_uid = fetch_and_print_new(client, last_seen_uid)

                    # --- IDLE explícito (sin context manager) ---
                    client.idle()
                    try:
                        responses = client.idle_check(timeout=IDLE_SECS)
                    finally:
                        try:
                            client.idle_done()
                        except Exception:
                            pass
                    # -------------------------------------------

                    if responses:
                        last_seen_uid = fetch_and_print_new(client, last_seen_uid)
                    # si no hubo respuestas (timeout), el bucle reinicia IDLE y mantiene viva la sesión

        except KeyboardInterrupt:
            print("\nSaliendo…")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}. Reintentando en 10s…")
            time.sleep(10)

if __name__ == "__main__":
    main()
