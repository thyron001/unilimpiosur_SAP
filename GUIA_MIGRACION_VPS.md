# 🚀 Guía Completa de Migración a VPS - UnilimpioSur SAP

Esta guía te ayudará a migrar completamente tu sistema UnilimpioSur SAP desde tu entorno local a un VPS.

## 📋 Tabla de Contenidos

1. [Preparación](#preparación)
2. [Exportación de Base de Datos](#exportación-de-base-de-datos)
3. [Transferencia al VPS](#transferencia-al-vps)
4. [Instalación en VPS](#instalación-en-vps)
5. [Configuración Final](#configuración-final)
6. [Verificación](#verificación)
7. [Troubleshooting](#troubleshooting)

---

## 🛠️ Preparación

### Requisitos del VPS

**Especificaciones mínimas recomendadas:**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Almacenamiento**: 20GB SSD
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior

**Software requerido:**
- PostgreSQL 12+
- Python 3.8+
- Git (opcional, para clonar repositorios)

### Archivos necesarios en tu máquina local

Asegúrate de tener estos archivos en tu proyecto:
- `exportar_bd.py` - Script de exportación
- `importar_bd_vps.py` - Script de importación
- `configuracion_ejemplo.env` - Variables de entorno
- Todo el código fuente del proyecto

---

## 📤 Exportación de Base de Datos

### Paso 1: Ejecutar el script de exportación

```bash
# En tu máquina local, en el directorio del proyecto
py exportar_bd.py
```

Este script creará un directorio `backup_bd_YYYYMMDD_HHMMSS` con:

```
backup_bd_20241215_143022/
├── 01_estructura.sql      # Estructura de la base de datos
├── 02_datos.sql           # Datos de la base de datos
├── 03_completo.sql        # Archivo completo (estructura + datos)
├── configuracion_vps.env  # Variables de entorno para VPS
├── instalar_en_vps.sh     # Script de instalación automática
└── README_MIGRACION.md    # Documentación detallada
```

### Paso 2: Comprimir los archivos

```bash
# Comprimir el directorio de backup
tar -czf backup_bd_20241215_143022.tar.gz backup_bd_20241215_143022/
```

### Paso 3: Verificar la exportación

```bash
# Verificar que el archivo se creó correctamente
ls -lh backup_bd_*.tar.gz

# Verificar contenido del backup
tar -tzf backup_bd_20241215_143022.tar.gz
```

---

## 📡 Transferencia al VPS

### Opción 1: SCP (Recomendado)

```bash
# Transferir el archivo comprimido al VPS
scp backup_bd_20241215_143022.tar.gz usuario@tu-vps-ip:/home/usuario/

# Transferir el código fuente del proyecto
scp -r . usuario@tu-vps-ip:/home/usuario/unilimpiosur_sap/
```

### Opción 2: SFTP

```bash
# Conectar por SFTP
sftp usuario@tu-vps-ip

# Dentro de SFTP
put backup_bd_20241215_143022.tar.gz
put -r . unilimpiosur_sap/
```

### Opción 3: Git (Si tienes repositorio)

```bash
# En el VPS, clonar el repositorio
git clone https://github.com/tu-usuario/unilimpiosur_sap.git
cd unilimpiosur_sap

# Transferir solo el backup
scp backup_bd_20241215_143022.tar.gz usuario@tu-vps-ip:/home/usuario/unilimpiosur_sap/
```

---

## 🖥️ Instalación en VPS

### Método 1: Instalación Automática (Recomendado)

```bash
# Conectar al VPS
ssh usuario@tu-vps-ip

# Descomprimir el backup
tar -xzf backup_bd_20241215_143022.tar.gz
cd backup_bd_20241215_143022/

# Hacer ejecutable el script de instalación
chmod +x instalar_en_vps.sh

# Ejecutar instalación automática
sudo ./instalar_en_vps.sh
```

### Método 2: Instalación Manual

#### Paso 1: Instalar dependencias del sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Instalar Python y dependencias
sudo apt install -y python3 python3-pip python3-venv

# Instalar herramientas adicionales
sudo apt install -y curl wget git
```

#### Paso 2: Configurar PostgreSQL

```bash
# Iniciar PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configurar usuario y base de datos
sudo -u postgres psql

-- Dentro de PostgreSQL
CREATE USER unilimpiosur_app WITH PASSWORD 'unilimpiosur_secure_2024';
CREATE DATABASE unilimpiosur_sap OWNER unilimpiosur_app;
GRANT ALL PRIVILEGES ON DATABASE unilimpiosur_sap TO unilimpiosur_app;
\q
```

#### Paso 3: Importar base de datos

```bash
# Descomprimir backup
tar -xzf backup_bd_20241215_143022.tar.gz
cd backup_bd_20241215_143022/

# Importar estructura
sudo -u postgres psql -d unilimpiosur_sap -f 01_estructura.sql

# Importar datos
sudo -u postgres psql -d unilimpiosur_sap -f 02_datos.sql

# Configurar permisos
sudo -u postgres psql -d unilimpiosur_sap -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unilimpiosur_app;"
sudo -u postgres psql -d unilimpiosur_sap -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unilimpiosur_app;"
```

#### Paso 4: Configurar aplicación

```bash
# Crear directorio de la aplicación
sudo mkdir -p /var/www/unilimpiosur
sudo chown $USER:$USER /var/www/unilimpiosur

# Copiar archivos del proyecto
cp -r /ruta/a/tu/proyecto/* /var/www/unilimpiosur/
cd /var/www/unilimpiosur

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## ⚙️ Configuración Final

### Paso 1: Configurar variables de entorno

```bash
# Copiar archivo de configuración
cp configuracion_vps.env .env

# Editar configuración
nano .env
```

**Configuraciones importantes a revisar:**

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=unilimpiosur_sap
DB_USER=unilimpiosur_app
DB_PASSWORD=unilimpiosur_secure_2024  # Cambiar por contraseña segura

# Aplicación
FLASK_HOST=0.0.0.0  # Importante: permitir conexiones externas
FLASK_PORT=5000
FLASK_SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui

# Archivos
UPLOAD_FOLDER=/var/www/unilimpiosur/uploads
SAP_FILES_FOLDER=/var/www/unilimpiosur/sap_files
```

### Paso 2: Crear directorios necesarios

```bash
# Crear directorios de trabajo
mkdir -p /var/www/unilimpiosur/{uploads,sap_files,logs}

# Configurar permisos
chmod 755 /var/www/unilimpiosur
chmod 755 /var/www/unilimpiosur/uploads
chmod 755 /var/www/unilimpiosur/sap_files
```

### Paso 3: Configurar servicio systemd

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/unilimpiosur.service
```

**Contenido del servicio:**

```ini
[Unit]
Description=UnilimpioSur SAP System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/unilimpiosur
Environment=PATH=/var/www/unilimpiosur/venv/bin
ExecStart=/var/www/unilimpiosur/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Paso 4: Habilitar y iniciar servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable unilimpiosur

# Iniciar servicio
sudo systemctl start unilimpiosur

# Verificar estado
sudo systemctl status unilimpiosur
```

### Paso 5: Configurar firewall

```bash
# Instalar UFW si no está instalado
sudo apt install -y ufw

# Configurar reglas básicas
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH
sudo ufw allow ssh

# Permitir puerto de la aplicación
sudo ufw allow 5000/tcp

# Activar firewall
sudo ufw enable

# Verificar estado
sudo ufw status
```

---

## 🔍 Verificación

### Verificar base de datos

```bash
# Conectar a la base de datos
sudo -u postgres psql -d unilimpiosur_sap

-- Verificar tablas
\dt

-- Verificar datos
SELECT COUNT(*) FROM pedidos;
SELECT COUNT(*) FROM clientes;
SELECT COUNT(*) FROM productos;

-- Verificar configuración
SELECT * FROM configuracion;

\q
```

### Verificar aplicación

```bash
# Verificar que el servicio está ejecutándose
sudo systemctl status unilimpiosur

# Ver logs en tiempo real
sudo journalctl -u unilimpiosur -f

# Verificar que el puerto está abierto
sudo netstat -tlnp | grep :5000

# Probar conexión local
curl http://localhost:5000
```

### Verificar desde navegador

```
http://tu-vps-ip:5000
```

Deberías ver la interfaz de UnilimpioSur SAP funcionando correctamente.

---

## 🚨 Troubleshooting

### Problemas comunes y soluciones

#### 1. Error de conexión a base de datos

**Síntomas:**
```
psycopg.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Soluciones:**
```bash
# Verificar que PostgreSQL está ejecutándose
sudo systemctl status postgresql

# Iniciar PostgreSQL si no está ejecutándose
sudo systemctl start postgresql

# Verificar configuración de conexión
sudo nano /etc/postgresql/*/main/postgresql.conf

# Verificar configuración de autenticación
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

#### 2. Error de permisos en archivos

**Síntomas:**
```
PermissionError: [Errno 13] Permission denied
```

**Soluciones:**
```bash
# Verificar propietario de archivos
ls -la /var/www/unilimpiosur/

# Cambiar propietario
sudo chown -R www-data:www-data /var/www/unilimpiosur/

# Configurar permisos
sudo chmod -R 755 /var/www/unilimpiosur/
```

#### 3. Error de puerto en uso

**Síntomas:**
```
OSError: [Errno 98] Address already in use
```

**Soluciones:**
```bash
# Verificar qué proceso usa el puerto
sudo lsof -i :5000

# Matar proceso si es necesario
sudo kill -9 PID_DEL_PROCESO

# Reiniciar servicio
sudo systemctl restart unilimpiosur
```

#### 4. Error de módulos Python

**Síntomas:**
```
ModuleNotFoundError: No module named 'psycopg'
```

**Soluciones:**
```bash
# Activar entorno virtual
cd /var/www/unilimpiosur
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep psycopg
```

#### 5. Error de variables de entorno

**Síntomas:**
```
KeyError: 'DB_HOST'
```

**Soluciones:**
```bash
# Verificar archivo .env
cat /var/www/unilimpiosur/.env

# Verificar que el archivo existe
ls -la /var/www/unilimpiosur/.env

# Recargar variables de entorno
source /var/www/unilimpiosur/.env
```

### Comandos útiles para debugging

```bash
# Ver logs del servicio
sudo journalctl -u unilimpiosur -f

# Ver logs de PostgreSQL
sudo journalctl -u postgresql -f

# Verificar configuración de red
sudo netstat -tlnp

# Verificar uso de memoria
free -h

# Verificar uso de disco
df -h

# Verificar procesos Python
ps aux | grep python
```

---

## 🔒 Seguridad

### Recomendaciones de seguridad

1. **Cambiar contraseñas por defecto:**
   ```bash
   # Cambiar contraseña de PostgreSQL
   sudo -u postgres psql -c "ALTER USER unilimpiosur_app PASSWORD 'nueva_contraseña_segura';"
   
   # Actualizar archivo .env
   nano /var/www/unilimpiosur/.env
   ```

2. **Configurar SSL/TLS:**
   ```bash
   # Instalar certificado SSL (Let's Encrypt)
   sudo apt install -y certbot
   sudo certbot certonly --standalone -d tu-dominio.com
   ```

3. **Configurar backup automático:**
   ```bash
   # Crear script de backup
   sudo nano /usr/local/bin/backup_unilimpiosur.sh
   ```

4. **Configurar monitoreo:**
   ```bash
   # Instalar herramientas de monitoreo
   sudo apt install -y htop iotop nethogs
   ```

---

## 📞 Soporte

### Información para reportar problemas

Cuando reportes problemas, incluye:

1. **Información del sistema:**
   ```bash
   uname -a
   lsb_release -a
   ```

2. **Estado de servicios:**
   ```bash
   sudo systemctl status unilimpiosur
   sudo systemctl status postgresql
   ```

3. **Logs relevantes:**
   ```bash
   sudo journalctl -u unilimpiosur --since "1 hour ago"
   ```

4. **Configuración de red:**
   ```bash
   sudo netstat -tlnp
   ```

### Recursos adicionales

- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de systemd](https://systemd.io/)

---

## ✅ Checklist de Migración

- [ ] Base de datos exportada correctamente
- [ ] Archivos transferidos al VPS
- [ ] PostgreSQL instalado y configurado
- [ ] Base de datos importada
- [ ] Python y dependencias instaladas
- [ ] Variables de entorno configuradas
- [ ] Servicio systemd creado y habilitado
- [ ] Firewall configurado
- [ ] Aplicación accesible desde navegador
- [ ] Logs funcionando correctamente
- [ ] Backup automático configurado (opcional)
- [ ] SSL/TLS configurado (opcional)

---

*Documento generado para UnilimpioSur SAP - Sistema de Gestión de Pedidos*
*Fecha: $(date +%Y-%m-%d)*
