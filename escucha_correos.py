# escucha_correos.py
# Escucha IMAP; cuando llega un correo con PDF, lo parsea, imprime resumen
# y guarda en PostgreSQL. Usa el emparejador por NOMBRE y ALIAS (unidad+desc)
# contra la base de datos con soporte para alias de productos.

import os
import ssl
import time
import tempfile
import fcntl
import sys
from typing import Callable, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header, make_header

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# --- módulos del proyecto ---
from procesamiento_pedidos import (
    extraer_filas_pdf,
    emparejar_filas_con_bd,         # <- NUEVO: emparejador por nombre (BD)
    imprimir_filas,
    imprimir_filas_emparejadas,
    extraer_sucursal,
    imprimir_resumen_pedido,
)
from persistencia_postgresql import guardar_pedido

# --- Configuración (desde variables de entorno) ---
IMAP_SERVIDOR   = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USUARIO    = os.getenv("IMAP_USER")
IMAP_CLAVE      = os.getenv("IMAP_PASS")
IMAP_BUZON      = os.getenv("IMAP_MAILBOX", "INBOX")
TIEMPO_IDLE     = int(os.getenv("IMAP_IDLE_SECS", "1740"))  # 29 min por defecto
DEFAULT_CLIENTE = os.getenv("DEFAULT_CLIENTE", "Roldan")    # cliente por defecto para bodegas/emparejado
# Configuración de remitentes permitidos
REMITENTES_PERMITIDOS_STR = os.getenv("REMITENTES_PERMITIDOS", "tyminobra@outlook.es,@gruporoldan.com.ec")
REMITENTES_PERMITIDOS = [r.strip().lower() for r in REMITENTES_PERMITIDOS_STR.split(",") if r.strip()]

# ---------- Utilidades ----------

# Directorio para archivos de bloqueo
LOCK_DIR = tempfile.gettempdir()

# Zona horaria de Ecuador (GMT-5)
ECUADOR_TZ = timezone(timedelta(hours=-5))

def obtener_fecha_local() -> datetime:
    """Obtiene la fecha y hora actual en la zona horaria de Ecuador (GMT-5)"""
    return datetime.now(ECUADOR_TZ)

def obtener_timestamp_local() -> str:
    """Obtiene un timestamp formateado en la zona horaria de Ecuador (GMT-5)"""
    return obtener_fecha_local().strftime("%Y-%m-%d %H:%M:%S")

def log_imap(mensaje: str) -> None:
    """Función de logging que fuerza el flush para Docker"""
    timestamp = obtener_timestamp_local()
    mensaje_completo = f"[{timestamp}] [IMAP] {mensaje}"
    print(mensaje_completo, flush=True)
    sys.stdout.flush()

def _obtener_archivo_bloqueo(uid: int) -> str:
    """Obtiene la ruta del archivo de bloqueo para un UID específico"""
    return os.path.join(LOCK_DIR, f"correo_procesado_{uid}.lock")

def _correo_ya_procesado(uid: int) -> bool:
    """Verifica si un correo ya fue procesado"""
    archivo_lock = _obtener_archivo_bloqueo(uid)
    return os.path.exists(archivo_lock)

def _marcar_correo_procesado(uid: int) -> None:
    """Marca un correo como procesado creando un archivo de bloqueo"""
    archivo_lock = _obtener_archivo_bloqueo(uid)
    try:
        with open(archivo_lock, 'w') as f:
            f.write(f"Procesado el {obtener_fecha_local().isoformat()}")
    except Exception as e:
        print(f"⚠️  No se pudo crear archivo de bloqueo para UID {uid}: {e}")

def es_remitente_permitido(correo_remitente: str) -> bool:
    """
    Verifica si un remitente está en la lista de permitidos.
    Soporta tanto direcciones completas como dominios (que empiecen con @).
    """
    correo_lower = correo_remitente.lower()
    
    for remitente_permitido in REMITENTES_PERMITIDOS:
        if remitente_permitido.startswith("@"):
            # Es un dominio, verificar si el correo termina con ese dominio
            if correo_lower.endswith(remitente_permitido):
                return True
        else:
            # Es una dirección completa, comparar exactamente
            if correo_lower == remitente_permitido:
                return True
    
    return False

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
    # Buscar TODOS los correos (leídos y no leídos) del remitente autorizado
    # Esto asegura que no se pierda ningún correo importante
    todos_los_uids = cliente.search(["ALL"])
    nuevos_uids = [uid for uid in todos_los_uids if uid > ultimo_uid]
    if not nuevos_uids:
        return ultimo_uid

    log_imap(f"📧 Se encontraron {len(nuevos_uids)} correos nuevos (UIDs: {nuevos_uids})")

    # Traemos ENVELOPE, RFC822 (cuerpo crudo) y INTERNALDATE (fecha de llegada al servidor)
    respuesta = cliente.fetch(nuevos_uids, ["ENVELOPE", "RFC822", "INTERNALDATE"])

    for uid in sorted(nuevos_uids):
        sobre = respuesta[uid].get(b"ENVELOPE")
        crudo = respuesta[uid].get(b"RFC822", b"")
        fecha_llegada = respuesta[uid].get(b"INTERNALDATE")
        if not sobre:
            continue

        # Asunto
        asunto_raw = sobre.subject
        asunto = decodificar(asunto_raw.decode() if isinstance(asunto_raw, bytes) else asunto_raw)

        # Remitente formateado
        remitente = ""
        correo_remitente = ""
        if sobre.from_:
            frm = sobre.from_[0]
            nombre = (frm.name or b"").decode(errors="ignore") if isinstance(frm.name, bytes) else (frm.name or "")
            buzon = (frm.mailbox or b"").decode(errors="ignore")
            host = (frm.host or b"").decode(errors="ignore")
            nombre_limpio = decodificar(nombre).strip()
            correo_remitente = f"{buzon}@{host}" if buzon and host else ""
            remitente = (f"{nombre_limpio} <{correo_remitente}>" if nombre_limpio else correo_remitente) or "(desconocido)"

        # Validar que el remitente esté en la lista de permitidos
        if not es_remitente_permitido(correo_remitente):
            log_imap(f"🚫 Correo UID {uid} ignorado: remitente '{correo_remitente}' no está en la lista de permitidos")
            continue

        log_imap(f"📬 Correo recibido UID {uid}:")
        log_imap(f"   De: {remitente}")
        log_imap(f"   Asunto: {asunto}")
        log_imap(f"   Fecha del correo: {sobre.date or 'No disponible'}")
        log_imap(f"   Fecha de llegada al servidor: {fecha_llegada or 'No disponible'}")

        nombre_pdf, bytes_pdf = extraer_primer_pdf(crudo)

        # Usar la fecha de llegada al servidor como prioridad, luego la fecha del correo, y finalmente la fecha actual
        if fecha_llegada:
            fecha_correo = fecha_llegada
            log_imap(f"   ✅ Usando fecha de llegada al servidor: {fecha_correo}")
        elif sobre.date:
            fecha_correo = sobre.date
            log_imap(f"   ✅ Usando fecha del correo: {fecha_correo}")
        else:
            fecha_correo = obtener_fecha_local()
            log_imap(f"   ⚠️  Usando fecha actual como fallback: {fecha_correo}")
        
        meta = {
            "uid": int(uid),
            "fecha": fecha_correo,  # Usar fecha de llegada al servidor, fecha del correo, o fecha actual
            "asunto": asunto,                       # str
            "remitente": remitente,                 # str
        }

        if bytes_pdf:
            # Verificar si el correo ya fue procesado
            if _correo_ya_procesado(uid):
                log_imap(f"⏭️  Correo UID {uid} ya fue procesado anteriormente - omitiendo")
                continue
            
            log_imap(f"✅ Correo UID {uid} contiene PDF: '{nombre_pdf or 'adjunto.pdf'}' - iniciando procesamiento")
            try:
                # Marcar como procesado ANTES de procesar para evitar duplicados
                _marcar_correo_procesado(uid)
                al_encontrar_pdf(meta, nombre_pdf or "adjunto.pdf", bytes_pdf)
                log_imap(f"✅ Correo UID {uid} procesado exitosamente (mantenido como no leído)")
            except Exception as err_cb:
                log_imap(f"⚠️  Error en callback al_encontrar_pdf: {err_cb}")
                # En caso de error, eliminar el archivo de bloqueo para permitir reintento
                try:
                    archivo_lock = _obtener_archivo_bloqueo(uid)
                    if os.path.exists(archivo_lock):
                        os.remove(archivo_lock)
                except Exception:
                    pass
        else:
            log_imap(f"⚠️  Correo UID {uid} de remitente autorizado '{correo_remitente}' pero sin PDF adjunto")

    return max(ultimo_uid, max(nuevos_uids))

def iniciar_escucha_correos(al_encontrar_pdf: Callable[[Dict[str, Any], str, bytes], None]) -> None:
    log_imap("🚀 INICIANDO ESCUCHA DE CORREOS - HILO IMAP ACTIVO")
    
    if not IMAP_USUARIO or not IMAP_CLAVE:
        log_imap("❌ Faltan IMAP_USER/IMAP_PASS en variables de entorno. Escucha no iniciada.")
        return

    contexto = ssl.create_default_context()
    log_imap(f"Conectando a {IMAP_SERVIDOR} como {IMAP_USUARIO} ...")
    log_imap(f"📧 Remitentes permitidos: {', '.join(REMITENTES_PERMITIDOS)}")

    while True:
        try:
            with IMAPClient(IMAP_SERVIDOR, ssl=True, ssl_context=contexto, timeout=60) as cliente:
                cliente.login(IMAP_USUARIO, IMAP_CLAVE)
                cliente.select_folder(IMAP_BUZON)
                log_imap(f"Conectado. Escuchando en '{IMAP_BUZON}' (IDLE).")

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
                        log_imap(f"🔄 IDLE detectó cambios, revisando correos...")
                        ultimo_uid = _revisar_nuevos(cliente, ultimo_uid, al_encontrar_pdf)
                    else:
                        # Log de heartbeat cada 5 minutos para verificar que está funcionando
                        log_imap(f"💓 Heartbeat - Escuchando correos (último UID: {ultimo_uid})")

        except KeyboardInterrupt:
            log_imap("\n⏹️  Escucha detenida por el usuario.")
            break
        except Exception as e:
            log_imap(f"⚠️  Error en escucha IMAP: {e}. Reintentando en 10s…")
            time.sleep(10)

# ---------- Pipeline por defecto (para usar directamente este archivo) ----------

def _pipeline_guardar(meta: Dict[str, Any], nombre_pdf: str, bytes_pdf: bytes) -> None:
    print("\n================= NUEVO PDF DETECTADO =================")
    print(f"Asunto: {meta.get('asunto')} | Remitente: {meta.get('remitente')} | UID: {meta.get('uid')}")
    print(f"Adjunto: {nombre_pdf}")

    # Procesar todos los correos sin restricciones temporales
    uid_correo = meta.get("uid")
    print(f"📧 Procesando correo UID {uid_correo} sin restricciones temporales")

    # 1) Filas de productos desde PDF
    filas = extraer_filas_pdf(bytes_pdf)
    imprimir_filas(filas)

    # 2) Sucursal (necesario para mapear bodegas por sucursal si aplica)
    resumen = extraer_sucursal(bytes_pdf)
    imprimir_resumen_pedido(resumen)

    # 3) Emparejado contra BD por NOMBRE (unidad+descripción), cliente configurable
    filas_enriquecidas, suc, cliente_id = emparejar_filas_con_bd(
        filas,
        cliente_nombre=DEFAULT_CLIENTE,
        sucursal_alias=resumen.get("sucursal"),
        sucursal_ruc=resumen.get("ruc"),
        sucursal_encargado=resumen.get("encargado")
    )
    imprimir_filas_emparejadas(filas_enriquecidas)

    # 4) Verificar si se encontró la sucursal por alias
    sucursal_alias_pdf = resumen.get("sucursal")
    if sucursal_alias_pdf and not suc:
        # No se encontró coincidencia en el alias - marcar como error
        print(f"❌ ERROR: No se encontró sucursal con alias '{sucursal_alias_pdf}' en la base de datos")
        pedido = {
            "fecha": meta.get("fecha"),
            "sucursal": f"ERROR: Alias '{sucursal_alias_pdf}' no encontrado",
            "orden_compra": resumen.get("orden_compra"),  # número de orden de compra del PDF
        }
        try:
            pedido_id, numero_pedido, estado = guardar_pedido(pedido, filas_enriquecidas, cliente_id, None)
            print(f"⚠️  Pedido guardado con ERROR: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
        except Exception as e:
            print(f"❌ No se guardó el pedido con error: {e}")
        return

    # 5) Guardar en PostgreSQL
    sucursal_txt = suc.get("nombre") if suc else "SUCURSAL DESCONOCIDA"
    pedido = {
        "fecha": meta.get("fecha"),
        "sucursal": sucursal_txt,
        "orden_compra": resumen.get("orden_compra"),  # número de orden de compra del PDF
    }
    try:
        sucursal_id = suc.get("id") if suc else None
        pedido_id, numero_pedido, estado = guardar_pedido(pedido, filas_enriquecidas, cliente_id, sucursal_id)
        print(f"✅ Pedido guardado: ID={pedido_id}, N°={numero_pedido}, Estado={estado}")
    except Exception as e:
        print(f"❌ No se guardó el pedido: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando escucha de correos en modo standalone...")
    iniciar_escucha_correos(_pipeline_guardar)
