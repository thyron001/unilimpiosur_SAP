# escucha_correos.py
# Módulo que escucha la bandeja IMAP y detecta el PRIMER PDF de cada correo nuevo.
# Llama a un callback con los metadatos y los bytes del PDF.

import os
import ssl
import time
from typing import Callable, Dict, Any, Tuple
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header

# --- Configuración (desde variables de entorno) ---
IMAP_SERVIDOR = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USUARIO  = os.getenv("IMAP_USER")
IMAP_CLAVE    = os.getenv("IMAP_PASS")
IMAP_BUZON    = os.getenv("IMAP_MAILBOX", "INBOX")
TIEMPO_IDLE   = int(os.getenv("IMAP_IDLE_SECS", "1740"))  # 29 min por defecto

# ---------- Utilidades ----------
def decodificar(valor):
    if valor is None:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except Exception:
        return str(valor)

def decodificar_nombre_archivo(nombre):
    if not nombre:
        return ""
    try:
        return str(make_header(decode_header(nombre)))
    except Exception:
        return nombre

def extraer_primer_pdf(mensaje_crudo: bytes) -> Tuple[str | None, bytes | None]:
    """
    Devuelve (nombre_pdf, bytes_pdf) del primer PDF encontrado, o (None, None).
    """
    msg = message_from_bytes(mensaje_crudo)
    for parte in msg.walk():
        if parte.get_content_maintype() == "multipart":
            continue
        tipo = (parte.get_content_type() or "").lower()
        nombre = decodificar_nombre_archivo(parte.get_filename())
        es_pdf_tipo = tipo == "application/pdf"
        es_pdf_nombre = nombre.lower().endswith(".pdf") if nombre else False
        if es_pdf_tipo or es_pdf_nombre:
            try:
                contenido = parte.get_payload(decode=True)
            except Exception:
                contenido = None
            if contenido:
                if not nombre:
                    nombre = "adjunto.pdf"
                return nombre, contenido
    return None, None

# ---------- Núcleo del listener ----------
def _revisar_nuevos(cliente: IMAPClient, ultimo_uid: int, al_encontrar_pdf: Callable[[Dict[str, Any], str, bytes], None]) -> int:
    """
    Revisa correos NO LEÍDOS con UID > ultimo_uid.
    Si hay PDF, llama al callback: al_encontrar_pdf(meta, nombre_pdf, bytes_pdf).
    Retorna el nuevo ultimo_uid.
    """
    nuevos_uids = [uid for uid in cliente.search(["UNSEEN"]) if uid > ultimo_uid]
    if not nuevos_uids:
        return ultimo_uid

    respuesta = cliente.fetch(nuevos_uids, ["ENVELOPE", "RFC822"])

    for uid in sorted(nuevos_uids):
        sobre = respuesta[uid].get(b"ENVELOPE")
        crudo = respuesta[uid].get(b"RFC822", b"")
        if not sobre:
            continue

        # Metadatos básicos
        asunto = decodificar(sobre.subject.decode() if isinstance(sobre.subject, bytes) else sobre.subject)
        remitente = ""
        if sobre.from_:
            frm = sobre.from_[0]
            nombre = (frm.name or b"").decode(errors="ignore") if isinstance(frm.name, bytes) else (frm.name or "")
            buzon = (frm.mailbox or b"").decode(errors="ignore")
            host = (frm.host or b"").decode(errors="ignore")
            nombre_limpio = decodificar(nombre).strip()
            correo = f"{buzon}@{host}" if buzon and host else ""
            remitente = (f"{nombre_limpio} <{correo}>" if nombre_limpio else correo) or "(desconocido)"

        nombre_pdf, bytes_pdf = extraer_primer_pdf(crudo)

        meta = {
            "uid": int(uid),
            "fecha": sobre.date,      # datetime | None
            "asunto": asunto,         # str
            "remitente": remitente,   # str
        }

        if bytes_pdf:
            try:
                al_encontrar_pdf(meta, nombre_pdf or "adjunto.pdf", bytes_pdf)
            except Exception as err_cb:
                print(f"⚠️  Error en callback al_encontrar_pdf: {err_cb}")

    return max(ultimo_uid, max(nuevos_uids))

def iniciar_escucha_correos(al_encontrar_pdf: Callable[[Dict[str, Any], str, bytes], None]) -> None:
    """
    Bucle infinito que mantiene la sesión IMAP activa y llama al callback cuando llega un PDF.
    """
    if not IMAP_USUARIO or not IMAP_CLAVE:
        print("❌ Faltan IMAP_USER/IMAP_PASS en variables de entorno. Escucha no iniciada.")
        return

    contexto = ssl.create_default_context()
    print(f"Conectando a {IMAP_SERVIDOR} como {IMAP_USUARIO} ...")

    while True:
        try:
            with IMAPClient(IMAP_SERVIDOR, ssl=True, ssl_context=contexto, timeout=60) as cliente:
                cliente.login(IMAP_USUARIO, IMAP_CLAVE)
                cliente.select_folder(IMAP_BUZON)
                print(f"Conectado. Escuchando en '{IMAP_BUZON}' (IDLE).")

                estado = cliente.folder_status(IMAP_BUZON, [b"UIDNEXT"])
                ultimo_uid = (estado.get(b"UIDNEXT") or 1) - 1

                while True:
                    ultimo_uid = _revisar_nuevos(cliente, ultimo_uid, al_encontrar_pdf)
                    cliente.idle()
                    try:
                        respuestas = cliente.idle_check(timeout=TIEMPO_IDLE)
                    finally:
                        try:
                            cliente.idle_done()
                        except Exception:
                            pass
                    if respuestas:
                        ultimo_uid = _revisar_nuevos(cliente, ultimo_uid, al_encontrar_pdf)

        except KeyboardInterrupt:
            print("\n⏹️  Escucha detenida por el usuario.")
            break
        except Exception as e:
            print(f"⚠️  Error en escucha IMAP: {e}. Reintentando en 10s…")
            time.sleep(10)
