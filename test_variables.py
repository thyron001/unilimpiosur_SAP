#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que las variables de entorno estén correctamente configuradas
para el correo ventassur2@gmail.com
"""

import os
import sys

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno necesarias estén configuradas"""
    
    print("🔍 Verificando variables de entorno...")
    print("=" * 50)
    
    variables_requeridas = {
        'IMAP_HOST': 'imap.gmail.com',
        'IMAP_USER': 'ventassur2@unilimpio.com', 
        'IMAP_PASS': 'hgczxskkszfkxwrj',
        'IMAP_MAILBOX': 'INBOX',
        'IMAP_IDLE_SECS': '1740'
    }
    
    todas_correctas = True
    
    for variable, valor_esperado in variables_requeridas.items():
        valor_actual = os.getenv(variable)
        
        if valor_actual is None:
            print(f"❌ {variable}: NO CONFIGURADA")
            todas_correctas = False
        elif valor_actual == valor_esperado:
            if variable == 'IMAP_PASS':
                print(f"✅ {variable}: ✓ Configurada correctamente (valor oculto por seguridad)")
            else:
                print(f"✅ {variable}: {valor_actual}")
        else:
            print(f"⚠️  {variable}: {valor_actual} (esperado: {valor_esperado})")
            todas_correctas = False
    
    print("=" * 50)
    
    if todas_correctas:
        print("🎉 ¡Todas las variables están configuradas correctamente!")
        print("✅ El sistema puede conectarse al correo ventassur2@gmail.com")
        return True
    else:
        print("❌ Hay variables mal configuradas o faltantes")
        print("💡 Ejecuta: configurar_correo_ventassur.ps1")
        return False

def probar_conexion_imap():
    """Prueba la conexión IMAP con las variables configuradas"""
    
    print("\n🔌 Probando conexión IMAP...")
    print("=" * 50)
    
    try:
        import ssl
        from imapclient import IMAPClient
        
        host = os.getenv('IMAP_HOST', 'imap.gmail.com')
        user = os.getenv('IMAP_USER')
        password = os.getenv('IMAP_PASS')
        mailbox = os.getenv('IMAP_MAILBOX', 'INBOX')
        
        if not user or not password:
            print("❌ Faltan credenciales IMAP")
            return False
            
        print(f"🔗 Conectando a {host} como {user}...")
        
        context = ssl.create_default_context()
        
        with IMAPClient(host, ssl=True, ssl_context=context, timeout=30) as client:
            client.login(user, password)
            client.select_folder(mailbox)
            
            # Obtener información básica del buzón
            status = client.folder_status(mailbox, [b'MESSAGES', b'UNSEEN'])
            total_messages = status.get(b'MESSAGES', 0)
            unread_messages = status.get(b'UNSEEN', 0)
            
            print(f"✅ Conexión exitosa!")
            print(f"📧 Buzón: {mailbox}")
            print(f"📊 Total de mensajes: {total_messages}")
            print(f"📬 Mensajes no leídos: {unread_messages}")
            
        return True
        
    except ImportError:
        print("⚠️  imapclient no está instalado. Instala con: pip install imapclient")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de configuración para ventassur2@unilimpio.com")
    print("=" * 60)
    
    # Verificar variables de entorno
    variables_ok = verificar_variables_entorno()
    
    if variables_ok:
        # Probar conexión IMAP
        conexion_ok = probar_conexion_imap()
        
        if conexion_ok:
            print("\n🚀 ¡Sistema listo para funcionar!")
            print("Puedes ejecutar: py main.py")
        else:
            print("\n⚠️  Hay problemas de conexión. Verifica las credenciales.")
            sys.exit(1)
    else:
        print("\n❌ Configura las variables de entorno primero.")
        sys.exit(1)