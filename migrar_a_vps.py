#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para migrar UnilimpioSur SAP a VPS
Este script orquesta todo el proceso de migración
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def imprimir_banner():
    """Muestra el banner del script"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 UNILIMPIO SUR SAP                      ║
║                  MIGRACIÓN A VPS - WIZARD                    ║
║                                                              ║
║  Este script te ayudará a migrar tu sistema completo        ║
║  desde tu entorno local a un VPS de manera automatizada     ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def ejecutar_comando(comando, descripcion, mostrar_output=False):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {descripcion}...")
    try:
        if mostrar_output:
            resultado = subprocess.run(comando, shell=True, check=True)
        else:
            resultado = subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {descripcion} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {descripcion}:")
        if not mostrar_output and e.stderr:
            print(f"   Error: {e.stderr}")
        return False

def verificar_archivos_necesarios():
    """Verifica que todos los archivos necesarios estén presentes"""
    print("🔍 Verificando archivos necesarios...")
    
    archivos_requeridos = [
        "exportar_bd.py",
        "importar_bd_vps.py",
        "main.py",
        "requirements.txt",
        "configuracion_ejemplo.env"
    ]
    
    archivos_faltantes = []
    for archivo in archivos_requeridos:
        if not os.path.exists(archivo):
            archivos_faltantes.append(archivo)
        else:
            print(f"✅ {archivo}")
    
    if archivos_faltantes:
        print(f"❌ Archivos faltantes: {', '.join(archivos_faltantes)}")
        return False
    
    print("✅ Todos los archivos necesarios están presentes")
    return True

def exportar_base_datos():
    """Ejecuta la exportación de la base de datos"""
    print("\n📤 EXPORTANDO BASE DE DATOS")
    print("="*50)
    
    if not ejecutar_comando("py exportar_bd.py", "Exportando base de datos"):
        return False
    
    # Buscar el directorio de backup más reciente
    directorios_backup = [d for d in os.listdir('.') if d.startswith('backup_bd_') and os.path.isdir(d)]
    if not directorios_backup:
        print("❌ No se encontró el directorio de backup")
        return False
    
    directorio_backup = max(directorios_backup)
    print(f"✅ Backup creado en: {directorio_backup}")
    
    return directorio_backup

def comprimir_backup(directorio_backup):
    """Comprime el directorio de backup"""
    print(f"\n📦 COMPRIMIENDO BACKUP")
    print("="*50)
    
    nombre_archivo = f"{directorio_backup}.tar.gz"
    comando = f"tar -czf {nombre_archivo} {directorio_backup}"
    
    if not ejecutar_comando(comando, "Comprimiendo archivos de backup"):
        return False
    
    # Verificar que el archivo se creó
    if not os.path.exists(nombre_archivo):
        print(f"❌ No se pudo crear el archivo {nombre_archivo}")
        return False
    
    tamaño = os.path.getsize(nombre_archivo) / (1024 * 1024)  # MB
    print(f"✅ Archivo comprimido: {nombre_archivo} ({tamaño:.2f} MB)")
    
    return nombre_archivo

def mostrar_instrucciones_transferencia(archivo_comprimido):
    """Muestra las instrucciones para transferir archivos al VPS"""
    print(f"\n📡 TRANSFERENCIA AL VPS")
    print("="*50)
    print(f"Archivo a transferir: {archivo_comprimido}")
    print("\n📋 Opciones de transferencia:")
    
    print("\n1️⃣  SCP (Recomendado):")
    print(f"   scp {archivo_comprimido} usuario@tu-vps-ip:/home/usuario/")
    print("   scp -r . usuario@tu-vps-ip:/home/usuario/unilimpiosur_sap/")
    
    print("\n2️⃣  SFTP:")
    print("   sftp usuario@tu-vps-ip")
    print(f"   put {archivo_comprimido}")
    print("   put -r . unilimpiosur_sap/")
    
    print("\n3️⃣  Git (si tienes repositorio):")
    print("   git add .")
    print("   git commit -m 'Migración a VPS'")
    print("   git push")
    print("   # En el VPS: git pull")

def mostrar_instrucciones_instalacion():
    """Muestra las instrucciones para la instalación en el VPS"""
    print(f"\n🖥️  INSTALACIÓN EN VPS")
    print("="*50)
    
    print("📋 Pasos para completar la migración:")
    
    print("\n1️⃣  Conectar al VPS:")
    print("   ssh usuario@tu-vps-ip")
    
    print("\n2️⃣  Descomprimir backup:")
    print("   tar -xzf backup_bd_*.tar.gz")
    print("   cd backup_bd_*/")
    
    print("\n3️⃣  Instalación automática:")
    print("   chmod +x instalar_en_vps.sh")
    print("   sudo ./instalar_en_vps.sh")
    
    print("\n4️⃣  Instalación manual (alternativa):")
    print("   python3 importar_bd_vps.py")
    print("   # Seguir las instrucciones del script")
    
    print("\n5️⃣  Verificar instalación:")
    print("   sudo systemctl status unilimpiosur")
    print("   curl http://localhost:5000")

def crear_script_transferencia_automatica(archivo_comprimido):
    """Crea un script para transferir archivos automáticamente"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_name = f"transferir_a_vps_{timestamp}.sh"
    
    script_content = f"""#!/bin/bash
# Script para transferir UnilimpioSur SAP a VPS
# Generado automáticamente el {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

set -e

echo "🚀 Iniciando transferencia a VPS..."

# Colores para output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m'

print_status() {{
    echo -e "${{GREEN}}✅ $1${{NC}}"
}}

print_warning() {{
    echo -e "${{YELLOW}}⚠️  $1${{NC}}"
}}

print_error() {{
    echo -e "${{RED}}❌ $1${{NC}}"
}}

# Verificar que se proporcionó la IP del VPS
if [ -z "$1" ]; then
    print_error "Uso: $0 <ip-del-vps> [usuario]"
    echo "Ejemplo: $0 192.168.1.100 ubuntu"
    exit 1
fi

VPS_IP="$1"
VPS_USER="${{2:-ubuntu}}"

print_status "Configuración:"
echo "   • VPS IP: $VPS_IP"
echo "   • Usuario: $VPS_USER"
echo "   • Archivo: {archivo_comprimido}"
echo ""

# Verificar conectividad
print_status "Verificando conectividad con VPS..."
if ! ping -c 1 $VPS_IP > /dev/null 2>&1; then
    print_error "No se puede conectar al VPS $VPS_IP"
    exit 1
fi

# Transferir archivo comprimido
print_status "Transferiendo archivo de backup..."
scp {archivo_comprimido} $VPS_USER@$VPS_IP:/home/$VPS_USER/

# Transferir código fuente
print_status "Transferiendo código fuente..."
scp -r . $VPS_USER@$VPS_IP:/home/$VPS_USER/unilimpiosur_sap/

print_status "Transferencia completada!"
echo ""
print_warning "Próximos pasos en el VPS:"
echo "   1. ssh $VPS_USER@$VPS_IP"
echo "   2. tar -xzf {archivo_comprimido}"
echo "   3. cd backup_bd_*/"
echo "   4. chmod +x instalar_en_vps.sh"
echo "   5. sudo ./instalar_en_vps.sh"
echo ""
print_status "¡Migración iniciada exitosamente!"
"""
    
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Hacer el script ejecutable
    os.chmod(script_name, 0o755)
    
    print(f"✅ Script de transferencia creado: {script_name}")
    print(f"💡 Uso: ./{script_name} <ip-del-vps> [usuario]")
    
    return script_name

def main():
    """Función principal del script de migración"""
    imprimir_banner()
    
    print("🎯 Este script te guiará a través del proceso completo de migración")
    print("   desde tu entorno local a un VPS.")
    print()
    
    # Verificar archivos necesarios
    if not verificar_archivos_necesarios():
        print("\n❌ No se puede continuar sin todos los archivos necesarios")
        sys.exit(1)
    
    # Exportar base de datos
    directorio_backup = exportar_base_datos()
    if not directorio_backup:
        print("\n❌ Error en la exportación de la base de datos")
        sys.exit(1)
    
    # Comprimir backup
    archivo_comprimido = comprimir_backup(directorio_backup)
    if not archivo_comprimido:
        print("\n❌ Error comprimiendo el backup")
        sys.exit(1)
    
    # Crear script de transferencia automática
    script_transferencia = crear_script_transferencia_automatica(archivo_comprimido)
    
    # Mostrar instrucciones
    mostrar_instrucciones_transferencia(archivo_comprimido)
    mostrar_instrucciones_instalacion()
    
    # Resumen final
    print(f"\n🎉 MIGRACIÓN PREPARADA EXITOSAMENTE")
    print("="*50)
    print(f"📁 Archivos creados:")
    print(f"   • {directorio_backup}/ - Directorio de backup")
    print(f"   • {archivo_comprimido} - Backup comprimido")
    print(f"   • {script_transferencia} - Script de transferencia")
    print(f"   • GUIA_MIGRACION_VPS.md - Guía completa")
    print()
    print("🚀 Para completar la migración:")
    print(f"   1. Ejecutar: ./{script_transferencia} <ip-del-vps>")
    print("   2. Seguir las instrucciones en el VPS")
    print("   3. Verificar que la aplicación funciona")
    print()
    print("📖 Para más detalles, consulta: GUIA_MIGRACION_VPS.md")
    print("="*50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Migración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
