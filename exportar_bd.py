#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para exportar la base de datos de UnilimpioSur SAP
Incluye tanto la estructura como los datos para migración completa
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {descripcion}...")
    try:
        resultado = subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {descripcion} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {descripcion}:")
        print(f"   Comando: {comando}")
        print(f"   Error: {e.stderr}")
        return False

def exportar_base_datos():
    """Exporta la base de datos completa con estructura y datos"""
    
    # Obtener variables de entorno de la base de datos
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'unilimpiosur_sap')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # Verificar que tenemos las variables necesarias
    if not db_name:
        print("❌ Error: Variable DB_NAME no configurada")
        return False
    
    # Crear directorio para la exportación
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    directorio_export = Path(f"backup_bd_{timestamp}")
    directorio_export.mkdir(exist_ok=True)
    
    print(f"📁 Exportando a: {directorio_export}")
    
    # Configurar variables de entorno para pg_dump
    env = os.environ.copy()
    if db_password:
        env['PGPASSWORD'] = db_password
    
    # 1. Exportar solo la estructura (esquema)
    archivo_estructura = directorio_export / "01_estructura.sql"
    comando_estructura = f"pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} --schema-only --no-owner --no-privileges"
    
    if not ejecutar_comando(f"{comando_estructura} > {archivo_estructura}", "Exportando estructura de base de datos"):
        return False
    
    # 2. Exportar solo los datos
    archivo_datos = directorio_export / "02_datos.sql"
    comando_datos = f"pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} --data-only --no-owner --no-privileges"
    
    if not ejecutar_comando(f"{comando_datos} > {archivo_datos}", "Exportando datos de base de datos"):
        return False
    
    # 3. Exportar archivo completo (estructura + datos)
    archivo_completo = directorio_export / "03_completo.sql"
    comando_completo = f"pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} --no-owner --no-privileges"
    
    if not ejecutar_comando(f"{comando_completo} > {archivo_completo}", "Exportando archivo completo"):
        return False
    
    # 4. Crear archivo de configuración para el VPS
    archivo_config = directorio_export / "configuracion_vps.env"
    config_content = f"""# =====================================================
# CONFIGURACIÓN PARA VPS
# Sistema UnilimpioSur SAP - Base de Datos
# Generado: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# =====================================================

# Configuración de base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME={db_name}
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_SEGURO_AQUI

# Configuración de correo electrónico (IMAP)
IMAP_HOST=imap.gmail.com
IMAP_USER=ventassur2@unilimpio.com
IMAP_PASS=hgczxskkszfkxwrj
IMAP_MAILBOX=INBOX
IMAP_IDLE_SECS=1740

# Configuración de la aplicación Flask
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui

# Configuración de archivos
UPLOAD_FOLDER=/var/www/unilimpiosur/uploads
SAP_FILES_FOLDER=/var/www/unilimpiosur/sap_files

# =====================================================
# INSTRUCCIONES DE INSTALACIÓN EN VPS:
# =====================================================
# 1. Instalar PostgreSQL en el VPS
# 2. Crear usuario y base de datos
# 3. Ejecutar: psql -U postgres -d {db_name} -f 01_estructura.sql
# 4. Ejecutar: psql -U postgres -d {db_name} -f 02_datos.sql
# 5. Configurar las variables de entorno con este archivo
# 6. Instalar dependencias Python: pip install -r requirements.txt
# 7. Ejecutar la aplicación: python main.py
"""
    
    with open(archivo_config, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Archivo de configuración creado: {archivo_config}")
    
    # 5. Crear script de instalación automática
    archivo_instalacion = directorio_export / "instalar_en_vps.sh"
    script_content = f"""#!/bin/bash
# Script de instalación automática para VPS
# Sistema UnilimpioSur SAP

set -e

echo "🚀 Iniciando instalación de UnilimpioSur SAP en VPS..."

# Colores para output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Función para imprimir mensajes
print_status() {{
    echo -e "${{GREEN}}✅ $1${{NC}}"
}}

print_warning() {{
    echo -e "${{YELLOW}}⚠️  $1${{NC}}"
}}

print_error() {{
    echo -e "${{RED}}❌ $1${{NC}}"
}}

# Verificar que estamos como root o con sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root o con sudo"
    exit 1
fi

# Actualizar sistema
print_status "Actualizando sistema..."
apt update && apt upgrade -y

# Instalar PostgreSQL
print_status "Instalando PostgreSQL..."
apt install -y postgresql postgresql-contrib

# Instalar Python y pip
print_status "Instalando Python y dependencias..."
apt install -y python3 python3-pip python3-venv

# Crear usuario de sistema para la aplicación
print_status "Creando usuario del sistema..."
useradd -m -s /bin/bash unilimpiosur || true

# Crear directorios
print_status "Creando directorios..."
mkdir -p /var/www/unilimpiosur/{{uploads,sap_files,logs}}
chown -R unilimpiosur:unilimpiosur /var/www/unilimpiosur

# Configurar PostgreSQL
print_status "Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE USER unilimpiosur_app WITH PASSWORD 'unilimpiosur_secure_2024';"
sudo -u postgres psql -c "CREATE DATABASE {db_name} OWNER unilimpiosur_app;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO unilimpiosur_app;"

# Importar estructura de base de datos
print_status "Importando estructura de base de datos..."
sudo -u postgres psql -d {db_name} -f 01_estructura.sql

# Importar datos
print_status "Importando datos..."
sudo -u postgres psql -d {db_name} -f 02_datos.sql

# Configurar permisos en base de datos
print_status "Configurando permisos en base de datos..."
sudo -u postgres psql -d {db_name} -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unilimpiosur_app;"
sudo -u postgres psql -d {db_name} -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unilimpiosur_app;"

# Copiar archivos de la aplicación
print_status "Copiando archivos de la aplicación..."
cp -r ../* /var/www/unilimpiosur/
chown -R unilimpiosur:unilimpiosur /var/www/unilimpiosur

# Crear entorno virtual Python
print_status "Configurando entorno virtual Python..."
sudo -u unilimpiosur python3 -m venv /var/www/unilimpiosur/venv
sudo -u unilimpiosur /var/www/unilimpiosur/venv/bin/pip install -r /var/www/unilimpiosur/requirements.txt

# Configurar variables de entorno
print_status "Configurando variables de entorno..."
cp configuracion_vps.env /var/www/unilimpiosur/.env
chown unilimpiosur:unilimpiosur /var/www/unilimpiosur/.env
chmod 600 /var/www/unilimpiosur/.env

# Crear servicio systemd
print_status "Creando servicio systemd..."
cat > /etc/systemd/system/unilimpiosur.service << EOF
[Unit]
Description=UnilimpioSur SAP System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=unilimpiosur
Group=unilimpiosur
WorkingDirectory=/var/www/unilimpiosur
Environment=PATH=/var/www/unilimpiosur/venv/bin
ExecStart=/var/www/unilimpiosur/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar servicio
print_status "Habilitando servicio..."
systemctl daemon-reload
systemctl enable unilimpiosur
systemctl start unilimpiosur

# Configurar firewall (opcional)
print_warning "Configurando firewall..."
ufw allow 5000/tcp || true

# Mostrar estado del servicio
print_status "Verificando estado del servicio..."
systemctl status unilimpiosur --no-pager

echo ""
print_status "¡Instalación completada!"
echo ""
echo "📋 Información importante:"
echo "   • Servicio: systemctl status unilimpiosur"
echo "   • Logs: journalctl -u unilimpiosur -f"
echo "   • Reiniciar: systemctl restart unilimpiosur"
echo "   • Puerto: 5000"
echo "   • Base de datos: {db_name}"
echo ""
print_warning "Recuerda:"
echo "   1. Cambiar las contraseñas en /var/www/unilimpiosur/.env"
echo "   2. Configurar el dominio y SSL si es necesario"
echo "   3. Verificar que el puerto 5000 esté accesible"
"""
    
    with open(archivo_instalacion, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Hacer el script ejecutable
    os.chmod(archivo_instalacion, 0o755)
    
    print(f"✅ Script de instalación creado: {archivo_instalacion}")
    
    # 6. Crear README con instrucciones
    archivo_readme = directorio_export / "README_MIGRACION.md"
    readme_content = f"""# Migración de Base de Datos - UnilimpioSur SAP

Este directorio contiene todos los archivos necesarios para migrar la base de datos del sistema UnilimpioSur SAP a un VPS.

## 📁 Archivos incluidos

- `01_estructura.sql` - Estructura completa de la base de datos (tablas, índices, triggers, etc.)
- `02_datos.sql` - Todos los datos de la base de datos
- `03_completo.sql` - Archivo completo (estructura + datos)
- `configuracion_vps.env` - Variables de entorno para el VPS
- `instalar_en_vps.sh` - Script de instalación automática
- `README_MIGRACION.md` - Este archivo

## 🚀 Instalación Rápida (Automática)

1. Sube este directorio completo al VPS
2. Ejecuta el script de instalación:
   ```bash
   cd backup_bd_{timestamp}
   sudo chmod +x instalar_en_vps.sh
   sudo ./instalar_en_vps.sh
   ```

## 🔧 Instalación Manual

Si prefieres hacer la instalación paso a paso:

### 1. Instalar PostgreSQL
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

### 2. Crear base de datos y usuario
```bash
sudo -u postgres psql
CREATE USER unilimpiosur_app WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE {db_name} OWNER unilimpiosur_app;
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO unilimpiosur_app;
\\q
```

### 3. Importar estructura
```bash
sudo -u postgres psql -d {db_name} -f 01_estructura.sql
```

### 4. Importar datos
```bash
sudo -u postgres psql -d {db_name} -f 02_datos.sql
```

### 5. Configurar permisos
```bash
sudo -u postgres psql -d {db_name}
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unilimpiosur_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unilimpiosur_app;
\\q
```

### 6. Instalar aplicación
```bash
# Instalar Python y dependencias
sudo apt install -y python3 python3-pip python3-venv

# Crear directorio de la aplicación
sudo mkdir -p /var/www/unilimpiosur
sudo chown $USER:$USER /var/www/unilimpiosur

# Copiar archivos de la aplicación
cp -r /ruta/a/tu/proyecto/* /var/www/unilimpiosur/

# Crear entorno virtual
cd /var/www/unilimpiosur
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp configuracion_vps.env .env
# Editar .env con las configuraciones correctas
```

## 🔍 Verificación

Para verificar que la migración fue exitosa:

```bash
# Conectar a la base de datos
sudo -u postgres psql -d {db_name}

# Verificar tablas
\\dt

# Verificar datos
SELECT COUNT(*) FROM pedidos;
SELECT COUNT(*) FROM clientes;
SELECT COUNT(*) FROM productos;

# Verificar configuración
SELECT * FROM configuracion;
```

## 🚨 Troubleshooting

### Error de permisos en PostgreSQL
```bash
sudo -u postgres psql -d {db_name} -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unilimpiosur_app;"
```

### Error de conexión a la base de datos
- Verificar que PostgreSQL esté ejecutándose: `sudo systemctl status postgresql`
- Verificar configuración en `/etc/postgresql/*/main/postgresql.conf`
- Verificar configuración en `/etc/postgresql/*/main/pg_hba.conf`

### Error en la aplicación
- Verificar variables de entorno en `.env`
- Verificar logs: `journalctl -u unilimpiosur -f`
- Verificar permisos en directorios

## 📞 Soporte

Si encuentras problemas durante la migración, verifica:
1. Que todas las dependencias estén instaladas
2. Que las variables de entorno estén correctamente configuradas
3. Que los permisos de archivos y directorios sean correctos
4. Que PostgreSQL esté ejecutándose y aceptando conexiones

---
*Migración generada el: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(archivo_readme, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README de migración creado: {archivo_readme}")
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("🎉 EXPORTACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print(f"📁 Directorio: {directorio_export}")
    print(f"📄 Archivos creados:")
    print(f"   • {archivo_estructura.name} - Estructura de BD")
    print(f"   • {archivo_datos.name} - Datos de BD")
    print(f"   • {archivo_completo.name} - Archivo completo")
    print(f"   • {archivo_config.name} - Configuración VPS")
    print(f"   • {archivo_instalacion.name} - Script instalación")
    print(f"   • {archivo_readme.name} - Documentación")
    print("\n🚀 Para migrar al VPS:")
    print(f"   1. Comprimir: tar -czf backup_bd_{timestamp}.tar.gz {directorio_export}")
    print(f"   2. Subir al VPS")
    print(f"   3. Ejecutar: sudo ./instalar_en_vps.sh")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("🔄 Iniciando exportación de base de datos...")
    
    if exportar_base_datos():
        print("\n✅ Exportación completada exitosamente")
        sys.exit(0)
    else:
        print("\n❌ Error en la exportación")
        sys.exit(1)
