#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión IMAP
"""

import os
import ssl
from dotenv import load_dotenv
from imapclient import IMAPClient

# Cargar variables de entorno
load_dotenv()

def test_imap_connection():
    """Prueba la conexión IMAP con las credenciales configuradas"""
    
    IMAP_SERVIDOR = os.getenv("IMAP_HOST", "imap.gmail.com")
    IMAP_USUARIO = os.getenv("IMAP_USER")
    IMAP_CLAVE = os.getenv("IMAP_PASS")
    IMAP_BUZON = os.getenv("IMAP_MAILBOX", "INBOX")
    
    print(f"🔍 Probando conexión IMAP...")
    print(f"   Servidor: {IMAP_SERVIDOR}")
    print(f"   Usuario: {IMAP_USUARIO}")
    print(f"   Buzón: {IMAP_BUZON}")
    print(f"   Clave: {'*' * len(IMAP_CLAVE) if IMAP_CLAVE else 'NO CONFIGURADA'}")
    
    if not IMAP_USUARIO or not IMAP_CLAVE:
        print("❌ ERROR: Faltan credenciales IMAP_USER o IMAP_PASS")
        return False
    
    try:
        contexto = ssl.create_default_context()
        print(f"🔗 Conectando a {IMAP_SERVIDOR}...")
        
        with IMAPClient(IMAP_SERVIDOR, ssl=True, ssl_context=contexto, timeout=30) as cliente:
            print("✅ Conexión SSL establecida")
            
            print(f"🔐 Autenticando como {IMAP_USUARIO}...")
            cliente.login(IMAP_USUARIO, IMAP_CLAVE)
            print("✅ Autenticación exitosa")
            
            print(f"📁 Seleccionando buzón '{IMAP_BUZON}'...")
            cliente.select_folder(IMAP_BUZON)
            print("✅ Buzón seleccionado")
            
            # Obtener información del buzón
            estado = cliente.folder_status(IMAP_BUZON, [b"UIDNEXT", b"MESSAGES"])
            uidnext = estado.get(b"UIDNEXT", 0)
            messages = estado.get(b"MESSAGES", 0)
            
            print(f"📊 Información del buzón:")
            print(f"   Total de mensajes: {messages}")
            print(f"   Siguiente UID: {uidnext}")
            
            # Buscar algunos correos recientes
            print(f"🔍 Buscando correos recientes...")
            uids = cliente.search(["ALL"])
            print(f"   Correos encontrados: {len(uids)}")
            
            if uids:
                # Obtener información de los últimos 5 correos
                ultimos_uids = sorted(uids)[-5:]
                print(f"   Últimos 5 UIDs: {ultimos_uids}")
                
                # Obtener información básica de los últimos correos
                respuesta = cliente.fetch(ultimos_uids, ["ENVELOPE"])
                for uid in ultimos_uids:
                    sobre = respuesta[uid].get(b"ENVELOPE")
                    if sobre:
                        remitente = sobre.from_[0] if sobre.from_ else "Desconocido"
                        asunto = sobre.subject.decode() if sobre.subject else "Sin asunto"
                        fecha = sobre.date
                        print(f"   UID {uid}: {remitente.mailbox}@{remitente.host} - {asunto[:50]}... - {fecha}")
            
            print("✅ Prueba de conexión IMAP completada exitosamente")
            return True
            
    except Exception as e:
        print(f"❌ ERROR en conexión IMAP: {e}")
        print(f"   Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DE CONEXIÓN IMAP")
    print("=" * 60)
    
    success = test_imap_connection()
    
    print("=" * 60)
    if success:
        print("✅ PRUEBA EXITOSA - La conexión IMAP funciona correctamente")
    else:
        print("❌ PRUEBA FALLIDA - Revisar configuración IMAP")
    print("=" * 60)
