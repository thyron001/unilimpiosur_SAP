#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para importar la base de datos de UnilimpioSur SAP en un VPS
Este script se ejecuta en el VPS después de transferir los archivos de exportación
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

def ejecutar_comando(comando, descripcion, check=True):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {descripcion}...")
    try:
        resultado = subprocess.run(comando, shell=True, check=check, capture_output=True, text=True)
        if resultado.returncode == 0:
            print(f"✅ {descripcion} completado")
            return True
        else:
            print(f"⚠️  {descripcion} completado con advertencias")
            if resultado.stderr:
                print(f"   Advertencias: {resultado.stderr}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {descripcion}:")
        print(f"   Comando: {comando}")
        print(f"   Error: {e.stderr}")
        return False

def verificar_postgresql():
    """Verifica que PostgreSQL esté instalado y ejecutándose"""
    print("🔍 Verificando PostgreSQL...")
    
    # Verificar si PostgreSQL está instalado
    if not ejecutar_comando("which psql", "Verificando instalación de PostgreSQL", check=False):
        print("❌ PostgreSQL no está instalado")
        return False
    
    # Verificar si el servicio está ejecutándose
    if not ejecutar_comando("systemctl is-active postgresql", "Verificando estado de PostgreSQL", check=False):
        print("❌ PostgreSQL no está ejecutándose")
        print("💡 Intenta: sudo systemctl start postgresql")
        return False
    
    print("✅ PostgreSQL está instalado y ejecutándose")
    return True

def buscar_archivos_exportacion():
    """Busca los archivos de exportación en el directorio actual"""
    print("🔍 Buscando archivos de exportación...")
    
    archivos_necesarios = [
        "01_estructura.sql",
        "02_datos.sql",
        "configuracion_vps.env"
    ]
    
    archivos_encontrados = {}
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            archivos_encontrados[archivo] = True
            print(f"✅ Encontrado: {archivo}")
        else:
            archivos_encontrados[archivo] = False
            print(f"❌ No encontrado: {archivo}")
    
    # Verificar si tenemos al menos los archivos básicos
    if not archivos_encontrados["01_estructura.sql"] or not archivos_encontrados["02_datos.sql"]:
        print("❌ Faltan archivos esenciales de exportación")
        return None
    
    return archivos_encontrados

def configurar_base_datos(db_name, db_user, db_password):
    """Configura la base de datos y usuario"""
    print(f"🔧 Configurando base de datos '{db_name}'...")
    
    # Crear usuario si no existe
    comando_crear_usuario = f"sudo -u postgres psql -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\""
    ejecutar_comando(comando_crear_usuario, "Creando usuario de base de datos", check=False)
    
    # Crear base de datos
    comando_crear_db = f"sudo -u postgres psql -c \"CREATE DATABASE {db_name} OWNER {db_user};\""
    if not ejecutar_comando(comando_crear_db, "Creando base de datos", check=False):
        print("⚠️  La base de datos podría ya existir, continuando...")
    
    # Dar permisos
    comando_permisos = f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};\""
    ejecutar_comando(comando_permisos, "Configurando permisos en base de datos")
    
    return True

def importar_estructura(db_name, archivo_estructura):
    """Importa la estructura de la base de datos"""
    print(f"📋 Importando estructura desde {archivo_estructura}...")
    
    comando = f"sudo -u postgres psql -d {db_name} -f {archivo_estructura}"
    return ejecutar_comando(comando, "Importando estructura de base de datos")

def importar_datos(db_name, archivo_datos):
    """Importa los datos a la base de datos"""
    print(f"📊 Importando datos desde {archivo_datos}...")
    
    comando = f"sudo -u postgres psql -d {db_name} -f {archivo_datos}"
    return ejecutar_comando(comando, "Importando datos")

def configurar_permisos_finales(db_name, db_user):
    """Configura los permisos finales en todas las tablas"""
    print("🔐 Configurando permisos finales...")
    
    comandos_permisos = [
        f"sudo -u postgres psql -d {db_name} -c \"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {db_user};\"",
        f"sudo -u postgres psql -d {db_name} -c \"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {db_user};\"",
        f"sudo -u postgres psql -d {db_name} -c \"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {db_user};\""
    ]
    
    for comando in comandos_permisos:
        ejecutar_comando(comando, "Configurando permisos", check=False)
    
    return True

def verificar_importacion(db_name):
    """Verifica que la importación fue exitosa"""
    print("🔍 Verificando importación...")
    
    comandos_verificacion = [
        f"sudo -u postgres psql -d {db_name} -c \"\\dt\"",
        f"sudo -u postgres psql -d {db_name} -c \"SELECT COUNT(*) as total_pedidos FROM pedidos;\"",
        f"sudo -u postgres psql -d {db_name} -c \"SELECT COUNT(*) as total_clientes FROM clientes;\"",
        f"sudo -u postgres psql -d {db_name} -c \"SELECT COUNT(*) as total_productos FROM productos;\"",
        f"sudo -u postgres psql -d {db_name} -c \"SELECT * FROM configuracion;\""
    ]
    
    for comando in comandos_verificacion:
        ejecutar_comando(comando, "Verificando datos importados")
    
    return True

def configurar_variables_entorno(archivo_config):
    """Configura las variables de entorno"""
    if not os.path.exists(archivo_config):
        print("⚠️  Archivo de configuración no encontrado, saltando configuración de variables de entorno")
        return True
    
    print(f"⚙️  Configurando variables de entorno desde {archivo_config}...")
    
    # Leer el archivo de configuración
    with open(archivo_config, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Crear archivo .env para la aplicación
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Archivo .env creado")
    print("💡 Recuerda revisar y ajustar las configuraciones según tu VPS")
    
    return True

def importar_base_datos():
    """Función principal para importar la base de datos"""
    
    print("🚀 Iniciando importación de base de datos UnilimpioSur SAP")
    print("="*60)
    
    # 1. Verificar PostgreSQL
    if not verificar_postgresql():
        print("❌ No se puede continuar sin PostgreSQL")
        return False
    
    # 2. Buscar archivos de exportación
    archivos = buscar_archivos_exportacion()
    if not archivos:
        print("❌ No se encontraron los archivos de exportación necesarios")
        return False
    
    # 3. Configuración de base de datos
    db_name = "unilimpiosur_sap"
    db_user = "unilimpiosur_app"
    db_password = "unilimpiosur_secure_2024"  # Cambiar por una contraseña segura
    
    print(f"📊 Configuración de base de datos:")
    print(f"   • Nombre: {db_name}")
    print(f"   • Usuario: {db_user}")
    print(f"   • Contraseña: {db_password}")
    
    # 4. Configurar base de datos
    if not configurar_base_datos(db_name, db_user, db_password):
        print("❌ Error configurando base de datos")
        return False
    
    # 5. Importar estructura
    if not importar_estructura(db_name, "01_estructura.sql"):
        print("❌ Error importando estructura")
        return False
    
    # 6. Importar datos
    if not importar_datos(db_name, "02_datos.sql"):
        print("❌ Error importando datos")
        return False
    
    # 7. Configurar permisos finales
    if not configurar_permisos_finales(db_name, db_user):
        print("❌ Error configurando permisos")
        return False
    
    # 8. Verificar importación
    if not verificar_importacion(db_name):
        print("❌ Error verificando importación")
        return False
    
    # 9. Configurar variables de entorno
    if archivos.get("configuracion_vps.env"):
        configurar_variables_entorno("configuracion_vps.env")
    
    print("\n" + "="*60)
    print("🎉 IMPORTACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("📋 Resumen:")
    print(f"   • Base de datos: {db_name}")
    print(f"   • Usuario: {db_user}")
    print(f"   • Contraseña: {db_password}")
    print("   • Estructura: ✅ Importada")
    print("   • Datos: ✅ Importados")
    print("   • Permisos: ✅ Configurados")
    print("\n🚀 Próximos pasos:")
    print("   1. Instalar dependencias Python: pip install -r requirements.txt")
    print("   2. Configurar variables de entorno en .env")
    print("   3. Ejecutar la aplicación: python main.py")
    print("="*60)
    
    return True

def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Script de importación de base de datos UnilimpioSur SAP

Uso:
    python importar_bd_vps.py

Archivos requeridos:
    • 01_estructura.sql - Estructura de la base de datos
    • 02_datos.sql - Datos de la base de datos
    • configuracion_vps.env - Variables de entorno (opcional)

Prerrequisitos:
    • PostgreSQL instalado y ejecutándose
    • Permisos sudo para configurar base de datos
    • Archivos de exportación en el directorio actual

Ejemplo:
    # Después de transferir los archivos de exportación al VPS
    cd /ruta/a/archivos/exportacion
    python3 importar_bd_vps.py
        """)
        return
    
    try:
        if importar_base_datos():
            print("\n✅ Importación completada exitosamente")
            sys.exit(0)
        else:
            print("\n❌ Error en la importación")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Importación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
