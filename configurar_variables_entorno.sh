#!/bin/bash

# =====================================================
# SCRIPT DE CONFIGURACIÓN DE VARIABLES DE ENTORNO
# Sistema UnilimpioSur SAP - VPS
# =====================================================
# 
# Este script configura las variables de entorno
# necesarias para el funcionamiento del sistema.
# 
# INSTRUCCIONES DE USO:
# 1. Ejecutar como root o con sudo
# 2. Ajustar los valores según tu configuración
# 3. Reiniciar el servicio de la aplicación
# 
# =====================================================

echo "🔧 Configurando variables de entorno para UnilimpioSur SAP..."

# =====================================================
# 1. CONFIGURACIÓN DE BASE DE DATOS
# =====================================================

# Configuración de PostgreSQL
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="unilimpiosur_sap"
export DB_USER="unilimpiosur_app"
export DB_PASSWORD="tu_password_seguro_aqui"

# =====================================================
# 2. CONFIGURACIÓN DE CORREO ELECTRÓNICO
# =====================================================

# Configuración de Gmail para escucha de correos
export EMAIL_HOST="imap.gmail.com"
export EMAIL_PORT="993"
export EMAIL_USER="tu_email@gmail.com"
export EMAIL_PASSWORD="tu_app_password_aqui"
export EMAIL_FOLDER="INBOX"

# =====================================================
# 3. CONFIGURACIÓN DE LA APLICACIÓN
# =====================================================

# Configuración del servidor Flask
export FLASK_APP="main.py"
export FLASK_ENV="production"
export FLASK_DEBUG="False"
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

# Configuración de archivos
export UPLOAD_FOLDER="/var/www/unilimpiosur/uploads"
export SAP_FILES_FOLDER="/var/www/unilimpiosur/sap_files"

# =====================================================
# 4. CONFIGURACIÓN DE SEGURIDAD
# =====================================================

# Clave secreta para Flask (generar una nueva)
export FLASK_SECRET_KEY="tu_clave_secreta_muy_larga_y_segura_aqui"

# =====================================================
# 5. CREAR ARCHIVO .env
# =====================================================

ENV_FILE="/var/www/unilimpiosur/.env"

echo "📝 Creando archivo .env en $ENV_FILE..."

cat > "$ENV_FILE" << EOF
# =====================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# =====================================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO
# =====================================================
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT
EMAIL_USER=$EMAIL_USER
EMAIL_PASSWORD=$EMAIL_PASSWORD
EMAIL_FOLDER=$EMAIL_FOLDER

# =====================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =====================================================
FLASK_APP=$FLASK_APP
FLASK_ENV=$FLASK_ENV
FLASK_DEBUG=$FLASK_DEBUG
FLASK_HOST=$FLASK_HOST
FLASK_PORT=$FLASK_PORT
FLASK_SECRET_KEY=$FLASK_SECRET_KEY

# =====================================================
# CONFIGURACIÓN DE ARCHIVOS
# =====================================================
UPLOAD_FOLDER=$UPLOAD_FOLDER
SAP_FILES_FOLDER=$SAP_FILES_FOLDER
EOF

# =====================================================
# 6. CONFIGURAR PERMISOS
# =====================================================

echo "🔐 Configurando permisos..."

# Crear directorios si no existen
mkdir -p "$UPLOAD_FOLDER"
mkdir -p "$SAP_FILES_FOLDER"

# Configurar permisos
chown -R www-data:www-data /var/www/unilimpiosur/
chmod -R 755 /var/www/unilimpiosur/
chmod 600 "$ENV_FILE"

# =====================================================
# 7. CONFIGURAR SYSTEMD SERVICE
# =====================================================

echo "⚙️ Configurando servicio systemd..."

SERVICE_FILE="/etc/systemd/system/unilimpiosur.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=UnilimpioSur SAP Application
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/unilimpiosur
Environment=PATH=/var/www/unilimpiosur/venv/bin
EnvironmentFile=/var/www/unilimpiosur/.env
ExecStart=/var/www/unilimpiosur/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar servicio
systemctl daemon-reload
systemctl enable unilimpiosur

echo "✅ Configuración completada!"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Ajustar las variables en $ENV_FILE según tu configuración"
echo "2. Instalar dependencias Python: pip install -r requirements.txt"
echo "3. Ejecutar migraciones de base de datos si es necesario"
echo "4. Iniciar el servicio: systemctl start unilimpiosur"
echo "5. Verificar estado: systemctl status unilimpiosur"
echo ""
echo "🔍 Para ver logs: journalctl -u unilimpiosur -f"
