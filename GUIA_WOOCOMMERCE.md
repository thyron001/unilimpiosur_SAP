# Guía de Integración WooCommerce - Hola Mundo

## 📋 Resumen

Esta es una integración básica de "Hola Mundo" entre tu sistema SAP y WooCommerce. Permite conectarse a una tienda WooCommerce y obtener información básica de productos y órdenes.

## 🚀 Pasos para Configurar

### 1. Configurar Variables de Entorno

1. Copia el archivo `configuracion_ejemplo.env` a `.env`:
   ```bash
   cp configuracion_ejemplo.env .env
   ```

2. Edita el archivo `.env` y configura las variables de WooCommerce:
   ```env
   WOOCOMMERCE_URL=https://tu-tienda.com
   WOOCOMMERCE_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   WOOCOMMERCE_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 2. Obtener Credenciales de WooCommerce

1. Ve a tu tienda WooCommerce
2. Navega a **WooCommerce > Configuración > Avanzado > REST API**
3. Haz clic en **"Crear una clave API"**
4. Configura:
   - **Descripción**: "Integración SAP UnilimpioSur"
   - **Usuario**: Selecciona un usuario administrador
   - **Permisos**: "Lectura/Escritura"
5. Copia la **Consumer Key** y **Consumer Secret**

### 3. Instalar Dependencias

Las dependencias ya están instaladas, pero si necesitas reinstalar:
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la Aplicación

```bash
python main.py
```

## 🎯 Cómo Usar la Integración

### Acceder a WooCommerce

1. Abre tu navegador y ve a `http://localhost:5000/woocommerce`
2. Verás la nueva sección "WooCommerce" en el menú principal

### Funcionalidades Disponibles

#### 🔌 Probar Conexión
- Haz clic en "Probar conexión" para verificar que la configuración es correcta
- El estado se mostrará como:
  - ✅ **Verde**: Conexión exitosa
  - ❌ **Rojo**: Error de conexión
  - 🔄 **Amarillo**: Probando conexión

#### 📦 Cargar Productos
- Obtiene los últimos 10 productos de tu tienda WooCommerce
- Muestra información como:
  - Nombre del producto
  - SKU
  - Precio
  - Stock disponible
  - Estado
  - Fecha de creación

#### 📋 Cargar Órdenes
- Obtiene las últimas 5 órdenes de WooCommerce
- Muestra información como:
  - Número de orden
  - Cliente
  - Email
  - Total
  - Fecha
  - Cantidad de productos

#### 🔍 Buscar
- Usa la barra de búsqueda para filtrar productos y órdenes por texto

## 🛠️ Estructura Técnica

### Archivos Modificados/Creados

1. **requirements.txt** - Agregada librería `woocommerce==3.0.0`
2. **configuracion_ejemplo.env** - Agregadas variables de WooCommerce
3. **main.py** - Agregadas rutas y funciones de WooCommerce
4. **templates/woocommerce.html** - Nueva página web para la integración

### Endpoints API Creados

- `GET /woocommerce` - Página principal de WooCommerce
- `GET /api/woocommerce/probar-conexion` - Prueba la conexión
- `GET /api/woocommerce/productos` - Obtiene productos
- `GET /api/woocommerce/ordenes` - Obtiene órdenes

## 🔧 Solución de Problemas

### Error: "No se pudo configurar el cliente WooCommerce"
- Verifica que las variables de entorno estén configuradas correctamente
- Asegúrate de que el archivo `.env` existe y tiene las credenciales

### Error: "Error HTTP: 401"
- Las credenciales de WooCommerce son incorrectas
- Verifica que el Consumer Key y Consumer Secret sean correctos
- Asegúrate de que la clave API tenga permisos de "Lectura/Escritura"

### Error: "Error HTTP: 404"
- La URL de WooCommerce es incorrecta
- Verifica que la URL termine con `/` y no tenga `/wp-json/wc/v3`

### Error: "Error de conexión"
- Verifica que tu tienda WooCommerce esté online
- Comprueba tu conexión a internet
- Asegúrate de que no haya firewall bloqueando la conexión

## 🚀 Próximos Pasos (Funcionalidades Avanzadas)

Esta es una integración básica. Las siguientes funcionalidades podrían implementarse:

1. **Sincronización Automática**
   - Crear productos en SAP desde WooCommerce
   - Sincronizar inventario entre sistemas

2. **Procesamiento de Órdenes**
   - Convertir órdenes de WooCommerce en pedidos SAP
   - Integrar con el sistema de procesamiento de pedidos existente

3. **Gestión de Clientes**
   - Sincronizar clientes entre WooCommerce y SAP
   - Mapear direcciones de envío con sucursales

4. **Reportes Integrados**
   - Dashboard con métricas de WooCommerce
   - Análisis de ventas combinado

## 📞 Soporte

Si tienes problemas con la integración:

1. Verifica los logs de la aplicación en la consola
2. Comprueba que todas las variables de entorno estén configuradas
3. Asegúrate de que WooCommerce esté funcionando correctamente
4. Revisa que la versión de WooCommerce sea compatible (3.0+)

---

**¡Felicidades! 🎉** Tu integración básica de WooCommerce está lista. Ahora puedes conectar tu sistema SAP con tu tienda online.
