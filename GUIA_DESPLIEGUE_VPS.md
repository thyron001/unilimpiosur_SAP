# 🚀 Guía de Despliegue en VPS - Sistema UnilimpioSur SAP

Esta guía te ayudará a desplegar el sistema UnilimpioSur SAP en un VPS (Ubuntu/Debian).

## 📋 Prerrequisitos

- VPS con Ubuntu 20.04+ o Debian 11+
- Acceso root o sudo
- Dominio configurado (opcional)
- Certificado SSL (recomendado)

## 🔧 Paso 1: Preparación del Servidor

### 1.1 Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Instalar dependencias del sistema
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

### 1.3 Configurar PostgreSQL
```bash
# Iniciar y habilitar PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Cambiar a usuario postgres
sudo -u postgres psql

# En la consola de PostgreSQL:
CREATE USER unilimpiosur_app WITH PASSWORD 'tu_password_seguro_aqui';
ALTER USER unilimpiosur_app CREATEDB;
\q
```

## 🗄️ Paso 2: Configuración de Base de Datos

### 2.1 Ejecutar script de configuración
```bash
# Copiar el archivo de configuración
sudo cp configurar_bd_postgresql.sql /tmp/

# Ejecutar como usuario postgres
sudo -u postgres psql -f /tmp/configurar_bd_postgresql.sql
```

### 2.2 Verificar configuración
```bash
sudo -u postgres psql -d unilimpiosur_sap -c "\dt"
```

## 📁 Paso 3: Despliegue de la Aplicación

### 3.1 Crear directorio de la aplicación
```bash
sudo mkdir -p /var/www/unilimpiosur
sudo chown -R www-data:www-data /var/www/unilimpiosur
```

### 3.2 Clonar o copiar archivos
```bash
# Si usas Git:
cd /var/www/unilimpiosur
sudo -u www-data git clone https://github.com/tu-usuario/unilimpiosur-sap.git .

# O copiar archivos manualmente:
# sudo cp -r /ruta/local/del/proyecto/* /var/www/unilimpiosur/
```

### 3.3 Configurar entorno virtual
```bash
cd /var/www/unilimpiosur
sudo -u www-data python3 -m venv venv
sudo -u www-data ./venv/bin/pip install --upgrade pip
sudo -u www-data ./venv/bin/pip install -r requirements.txt
```

## ⚙️ Paso 4: Configuración de Variables de Entorno

### 4.1 Ejecutar script de configuración
```bash
sudo chmod +x configurar_variables_entorno.sh
sudo ./configurar_variables_entorno.sh
```

### 4.2 Ajustar configuración manualmente
```bash
sudo nano /var/www/unilimpiosur/.env
```

**Variables importantes a configurar:**
- `DB_PASSWORD`: Contraseña de la base de datos
- `EMAIL_USER`: Tu email de Gmail
- `EMAIL_PASSWORD`: App password de Gmail
- `FLASK_SECRET_KEY`: Clave secreta para Flask

## 🔐 Paso 5: Configuración de Gmail

### 5.1 Habilitar autenticación de 2 factores
1. Ir a [myaccount.google.com](https://myaccount.google.com)
2. Seguridad → Verificación en 2 pasos
3. Activar la verificación en 2 pasos

### 5.2 Generar App Password
1. Seguridad → Contraseñas de aplicaciones
2. Seleccionar "Correo" y "Otro (nombre personalizado)"
3. Escribir "UnilimpioSur SAP"
4. Copiar la contraseña generada
5. Usar esta contraseña en `EMAIL_PASSWORD`

## 🚀 Paso 6: Configuración del Servicio

### 6.1 Iniciar el servicio
```bash
sudo systemctl start unilimpiosur
sudo systemctl enable unilimpiosur
```

### 6.2 Verificar estado
```bash
sudo systemctl status unilimpiosur
```

### 6.3 Ver logs
```bash
sudo journalctl -u unilimpiosur -f
```

## 🌐 Paso 7: Configuración de Nginx (Opcional)

### 7.1 Crear configuración de Nginx
```bash
sudo nano /etc/nginx/sites-available/unilimpiosur
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Configuración para archivos estáticos
    location /static {
        alias /var/www/unilimpiosur/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 7.2 Habilitar sitio
```bash
sudo ln -s /etc/nginx/sites-available/unilimpiosur /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Paso 8: Configuración SSL (Recomendado)

### 8.1 Instalar Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 8.2 Obtener certificado
```bash
sudo certbot --nginx -d tu-dominio.com
```

## 📊 Paso 9: Monitoreo y Mantenimiento

### 9.1 Comandos útiles
```bash
# Ver estado del servicio
sudo systemctl status unilimpiosur

# Reiniciar servicio
sudo systemctl restart unilimpiosur

# Ver logs en tiempo real
sudo journalctl -u unilimpiosur -f

# Ver logs de PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Verificar conexión a base de datos
sudo -u postgres psql -d unilimpiosur_sap -c "SELECT COUNT(*) FROM pedidos;"
```

### 9.2 Backup de base de datos
```bash
# Crear backup
sudo -u postgres pg_dump unilimpiosur_sap > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
sudo -u postgres psql unilimpiosur_sap < backup_archivo.sql
```

## 🐛 Solución de Problemas

### Error de conexión a base de datos
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar configuración de pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

### Error de permisos
```bash
# Corregir permisos
sudo chown -R www-data:www-data /var/www/unilimpiosur
sudo chmod -R 755 /var/www/unilimpiosur
```

### Error de correo electrónico
- Verificar que el App Password sea correcto
- Verificar que la autenticación de 2 factores esté activada
- Revisar logs del servicio para errores específicos

## 📈 Optimizaciones de Rendimiento

### PostgreSQL
```sql
-- En /etc/postgresql/*/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Nginx
```nginx
# En la configuración de Nginx
client_max_body_size 10M;
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

## 🔄 Actualizaciones

### Actualizar aplicación
```bash
cd /var/www/unilimpiosur
sudo -u www-data git pull origin main
sudo -u www-data ./venv/bin/pip install -r requirements.txt
sudo systemctl restart unilimpiosur
```

### Actualizar base de datos
```bash
# Si hay cambios en el esquema, ejecutar migraciones
sudo -u postgres psql -d unilimpiosur_sap -f migraciones.sql
```

## 📞 Soporte

Para soporte técnico o reportar problemas:
- Revisar logs del sistema
- Verificar configuración de variables de entorno
- Comprobar conectividad de red
- Validar permisos de archivos

---

**¡Despliegue completado!** 🎉

Tu sistema UnilimpioSur SAP debería estar funcionando en `http://tu-servidor:5000` o `https://tu-dominio.com`
