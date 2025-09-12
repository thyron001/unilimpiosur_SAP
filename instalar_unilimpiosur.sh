#!/bin/bash

# =====================================================
# SCRIPT DE INSTALACIÓN AUTOMATIZADA
# Sistema UnilimpioSur SAP - VPS Ubuntu/Debian
# =====================================================
# 
# Este script automatiza la instalación completa del sistema
# en un VPS Ubuntu/Debian.
# 
# USO: sudo ./instalar_unilimpiosur.sh
# 
# =====================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que se ejecute como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root o con sudo"
    exit 1
fi

print_status "🚀 Iniciando instalación de UnilimpioSur SAP..."

# =====================================================
# 1. ACTUALIZAR SISTEMA
# =====================================================

print_status "📦 Actualizando sistema..."
apt update && apt upgrade -y

# =====================================================
# 2. INSTALAR DEPENDENCIAS
# =====================================================

print_status "🔧 Instalando dependencias del sistema..."
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl wget

# =====================================================
# 3. CONFIGURAR POSTGRESQL
# =====================================================

print_status "🗄️ Configurando PostgreSQL..."

# Iniciar y habilitar PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Crear usuario de la aplicación
sudo -u postgres psql -c "CREATE USER unilimpiosur_app WITH PASSWORD 'UnilimpioSur2024!';" || true
sudo -u postgres psql -c "ALTER USER unilimpiosur_app CREATEDB;" || true

# =====================================================
# 4. CONFIGURAR BASE DE DATOS
# =====================================================

print_status "📊 Configurando base de datos..."

# Verificar que el archivo de configuración existe
if [ ! -f "configurar_bd_postgresql.sql" ]; then
    print_error "Archivo configurar_bd_postgresql.sql no encontrado"
    exit 1
fi

# Ejecutar script de configuración de base de datos
sudo -u postgres psql -f configurar_bd_postgresql.sql

print_success "Base de datos configurada correctamente"

# =====================================================
# 5. CREAR DIRECTORIO DE LA APLICACIÓN
# =====================================================

print_status "📁 Creando directorio de la aplicación..."
mkdir -p /var/www/unilimpiosur
chown -R www-data:www-data /var/www/unilimpiosur

# =====================================================
# 6. COPIAR ARCHIVOS DE LA APLICACIÓN
# =====================================================

print_status "📋 Copiando archivos de la aplicación..."

# Copiar archivos del proyecto actual
cp -r . /var/www/unilimpiosur/
chown -R www-data:www-data /var/www/unilimpiosur

# =====================================================
# 7. CONFIGURAR ENTORNO VIRTUAL
# =====================================================

print_status "🐍 Configurando entorno virtual Python..."

cd /var/www/unilimpiosur
sudo -u www-data python3 -m venv venv
sudo -u www-data ./venv/bin/pip install --upgrade pip

# Verificar que requirements.txt existe
if [ -f "requirements.txt" ]; then
    sudo -u www-data ./venv/bin/pip install -r requirements.txt
else
    print_warning "requirements.txt no encontrado, instalando dependencias básicas..."
    sudo -u www-data ./venv/bin/pip install Flask psycopg2-binary pandas openpyxl pdfplumber imapclient pyzmail36 python-dotenv requests
fi

# =====================================================
# 8. CONFIGURAR VARIABLES DE ENTORNO
# =====================================================

print_status "⚙️ Configurando variables de entorno..."

# Generar clave secreta aleatoria
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Crear archivo .env
cat > /var/www/unilimpiosur/.env << EOF
# =====================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=unilimpiosur_sap
DB_USER=unilimpiosur_app
DB_PASSWORD=UnilimpioSur2024!

# =====================================================
# CONFIGURACIÓN DE CORREO ELECTRÓNICO
# =====================================================
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password_aqui
EMAIL_FOLDER=INBOX

# =====================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =====================================================
FLASK_APP=main.py
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_SECRET_KEY=$SECRET_KEY

# =====================================================
# CONFIGURACIÓN DE ARCHIVOS
# =====================================================
UPLOAD_FOLDER=/var/www/unilimpiosur/uploads
SAP_FILES_FOLDER=/var/www/unilimpiosur/sap_files
EOF

# Crear directorios necesarios
mkdir -p /var/www/unilimpiosur/uploads
mkdir -p /var/www/unilimpiosur/sap_files
chown -R www-data:www-data /var/www/unilimpiosur
chmod 600 /var/www/unilimpiosur/.env

# =====================================================
# 9. CONFIGURAR SERVICIO SYSTEMD
# =====================================================

print_status "🔧 Configurando servicio systemd..."

cat > /etc/systemd/system/unilimpiosur.service << EOF
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

# =====================================================
# 10. CONFIGURAR NGINX
# =====================================================

print_status "🌐 Configurando Nginx..."

# Crear configuración de Nginx
cat > /etc/nginx/sites-available/unilimpiosur << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/unilimpiosur/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/unilimpiosur /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración y recargar
nginx -t
systemctl reload nginx

# =====================================================
# 11. INICIAR SERVICIOS
# =====================================================

print_status "🚀 Iniciando servicios..."

systemctl start unilimpiosur
systemctl enable nginx

# Esperar un momento para que el servicio se inicie
sleep 5

# Verificar estado
if systemctl is-active --quiet unilimpiosur; then
    print_success "Servicio UnilimpioSur iniciado correctamente"
else
    print_error "Error al iniciar el servicio UnilimpioSur"
    print_status "Revisando logs..."
    journalctl -u unilimpiosur --no-pager -l
    exit 1
fi

# =====================================================
# 12. VERIFICACIÓN FINAL
# =====================================================

print_status "🔍 Verificando instalación..."

# Verificar que la aplicación responde
if curl -s http://localhost:5000 > /dev/null; then
    print_success "Aplicación respondiendo correctamente"
else
    print_warning "La aplicación no responde en el puerto 5000"
fi

# Verificar base de datos
if sudo -u postgres psql -d unilimpiosur_sap -c "SELECT COUNT(*) FROM configuracion;" > /dev/null 2>&1; then
    print_success "Base de datos funcionando correctamente"
else
    print_warning "Problema con la conexión a la base de datos"
fi

# =====================================================
# 13. MOSTRAR INFORMACIÓN FINAL
# =====================================================

print_success "🎉 ¡Instalación completada exitosamente!"
echo ""
echo "📋 INFORMACIÓN IMPORTANTE:"
echo "=========================="
echo "🌐 URL de acceso: http://$(curl -s ifconfig.me):5000"
echo "📁 Directorio de la aplicación: /var/www/unilimpiosur"
echo "🗄️ Base de datos: unilimpiosur_sap"
echo "👤 Usuario de BD: unilimpiosur_app"
echo "🔑 Contraseña de BD: UnilimpioSur2024!"
echo ""
echo "⚙️ CONFIGURACIÓN PENDIENTE:"
echo "=========================="
echo "1. Editar /var/www/unilimpiosur/.env con tus datos:"
echo "   - EMAIL_USER: tu email de Gmail"
echo "   - EMAIL_PASSWORD: tu App Password de Gmail"
echo ""
echo "2. Reiniciar el servicio después de configurar:"
echo "   sudo systemctl restart unilimpiosur"
echo ""
echo "📊 COMANDOS ÚTILES:"
echo "=================="
echo "• Ver estado: sudo systemctl status unilimpiosur"
echo "• Ver logs: sudo journalctl -u unilimpiosur -f"
echo "• Reiniciar: sudo systemctl restart unilimpiosur"
echo "• Backup BD: sudo -u postgres pg_dump unilimpiosur_sap > backup.sql"
echo ""
echo "🔒 SEGURIDAD:"
echo "============"
echo "• Cambiar contraseña de la base de datos"
echo "• Configurar firewall si es necesario"
echo "• Configurar SSL con Let's Encrypt"
echo ""
print_success "¡Sistema listo para usar! 🚀"
