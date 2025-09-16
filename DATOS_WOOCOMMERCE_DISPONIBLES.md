# 📊 Datos Disponibles desde WooCommerce

## 🛒 **DATOS DE ÓRDENES (PEDIDOS)**

### 📋 **Información Básica**
- **ID**: Identificador único de la orden
- **Número**: Número de orden (generalmente igual al ID)
- **Estado**: `generado`, `procesando`, `completado`, `cancelado`, etc.
- **Moneda**: USD (en tu caso)
- **Total**: Precio total de la orden
- **Subtotal**: Subtotal sin impuestos
- **Impuestos**: Total de impuestos
- **Envío**: Costo de envío
- **Descuento**: Descuentos aplicados

### 📅 **Fechas**
- **Creada**: Fecha y hora de creación
- **Modificada**: Última modificación
- **Completada**: Fecha de completado (si aplica)
- **Pagada**: Fecha de pago (si aplica)

### 👤 **Información del Cliente (Billing)**
- **Nombre**: Nombre completo
- **Empresa**: Nombre de la empresa
- **Email**: Correo electrónico
- **Teléfono**: Número de teléfono
- **Dirección 1**: Dirección principal
- **Dirección 2**: Dirección secundaria
- **Ciudad**: Ciudad
- **Estado**: Estado/Provincia
- **Código Postal**: Código postal
- **País**: País

### 🚚 **Información de Envío (Shipping)**
- **Nombre**: Nombre para envío
- **Empresa**: Empresa para envío
- **Dirección 1**: Dirección de envío
- **Dirección 2**: Dirección secundaria de envío
- **Ciudad**: Ciudad de envío
- **Estado**: Estado de envío
- **Código Postal**: Código postal de envío
- **País**: País de envío

### 📦 **Productos en la Orden (Line Items)**
Para cada producto:
- **ID**: ID único del item en la orden
- **Nombre**: Nombre del producto
- **SKU**: Código SKU del producto
- **Cantidad**: Cantidad pedida
- **Precio unitario**: Precio por unidad
- **Total**: Total del item (cantidad × precio)
- **Impuestos**: Impuestos del item
- **Producto ID**: ID del producto en WooCommerce
- **Variación ID**: ID de variación (si aplica)
- **Metadatos**: Información adicional del producto

### 💰 **Información de Pago**
- **Método de pago**: `cod` (Cash on Delivery), `bacs`, `cheque`, etc.
- **Título del método**: Nombre descriptivo del método
- **ID de transacción**: ID de la transacción de pago

### 🚚 **Métodos de Envío**
- **Método**: Nombre del método de envío
- **Total**: Costo del envío
- **Impuestos**: Impuestos del envío

### 📝 **Notas**
- **Nota del cliente**: Comentarios del cliente
- **Notas internas**: Notas administrativas

### 🔗 **Metadatos Personalizados**
En tu caso específico, tienes metadatos importantes:
- **`_billing_codigointerno`**: Código interno del cliente (ej: "GOLDEN MATRIZ")
- **`billing_codigointerno`**: Código interno de facturación
- **`_license_no`**: Número de licencia (fecha)
- **`is_vat_exempt`**: Exento de IVA (sí/no)
- **Datos de atribución**: Información de cómo llegó el cliente

---

## 📦 **DATOS DE PRODUCTOS**

### 📦 **Información Básica**
- **ID**: Identificador único del producto
- **Nombre**: Nombre del producto
- **SKU**: Código SKU único
- **Slug**: URL amigable
- **Estado**: `publish`, `draft`, `private`
- **Tipo**: `simple`, `variable`, `grouped`, `external`
- **Precio regular**: Precio normal
- **Precio de venta**: Precio con descuento
- **Precio actual**: Precio final

### 📊 **Inventario**
- **Stock**: Cantidad en inventario
- **Estado de stock**: `instock`, `outofstock`, `onbackorder`
- **Gestión de stock**: Si se gestiona automáticamente
- **Stock bajo**: Cantidad mínima de stock
- **Stock backorders**: Permitir pedidos sin stock

### 📝 **Descripción**
- **Descripción corta**: Resumen del producto
- **Descripción larga**: Descripción completa

### 🏷️ **Categorías**
- **Categorías**: Lista de categorías asignadas
- **ID de categoría**: Identificador de cada categoría

### 🏪 **Atributos**
- **Atributos**: Características del producto (color, talla, etc.)
- **Opciones**: Valores disponibles para cada atributo

### 📅 **Fechas**
- **Creado**: Fecha de creación
- **Modificado**: Última modificación
- **En venta desde**: Fecha de inicio de venta
- **En venta hasta**: Fecha de fin de venta

### 🔗 **Metadatos Personalizados**
En tu caso, tienes precios específicos por cliente:
- **`_role_based_pricing_rules`**: Precios por rol de usuario
- **`_customer_based_pricing_rules`**: Precios por cliente específico
- **Precios personalizados**: `precio_jaher`, `precio_marcimex`, `precio_golden`, etc.
- **Impuesto**: Porcentaje de IVA
- **Indicador**: Tipo de impuesto

---

## 🎯 **DATOS CLAVE PARA INTEGRACIÓN CON SAP**

### 🔑 **Para Identificar Clientes**
1. **Email del cliente** (`billing.email`)
2. **Código interno** (`_billing_codigointerno`)
3. **Nombre de la empresa** (`billing.company`)
4. **Nombre completo** (`billing.first_name` + `billing.last_name`)

### 📦 **Para Mapear Productos**
1. **SKU del producto** (`line_items[].sku`)
2. **ID del producto** (`line_items[].product_id`)
3. **Nombre del producto** (`line_items[].name`)

### 🏪 **Para Identificar Sucursales**
1. **Dirección de envío** (`shipping.address_1`, `shipping.city`)
2. **Código interno** (`_billing_codigointerno`)
3. **Empresa** (`billing.company`)

### 💰 **Para Procesar Pedidos**
1. **Total de la orden** (`total`)
2. **Cantidad por producto** (`line_items[].quantity`)
3. **Precio unitario** (`line_items[].price`)
4. **Fecha de creación** (`date_created`)
5. **Nota del cliente** (`customer_note`)

---

## 🔄 **FLUJO DE INTEGRACIÓN SUGERIDO**

### 1. **Obtener Órdenes Nuevas**
```python
# Obtener órdenes con estado "generado"
ordenes = wcapi.get("orders", params={
    "status": "generado",
    "per_page": 50,
    "orderby": "date",
    "order": "asc"
})
```

### 2. **Procesar Cada Orden**
```python
for orden in ordenes.json():
    # Extraer datos del cliente
    cliente_email = orden['billing']['email']
    cliente_codigo = orden['meta_data'].get('_billing_codigointerno')
    
    # Extraer productos
    for item in orden['line_items']:
        sku = item['sku']
        cantidad = item['quantity']
        precio = item['price']
    
    # Crear pedido en SAP
    crear_pedido_sap(orden)
```

### 3. **Actualizar Estado**
```python
# Marcar orden como procesada en WooCommerce
wcapi.put(f"orders/{orden_id}", {
    "status": "procesando"
})
```

---

## 📋 **EJEMPLO DE DATOS REALES DE TU TIENDA**

### Orden #22593:
- **Cliente**: ADRIAN ZUMBA (Golden)
- **Email**: adrianzumba26@gmail.com
- **Código interno**: GOLDEN MATRIZ
- **Total**: $100.54
- **Productos**: 7 items
- **Nota**: "pedido urdesa"

### Productos en la orden:
1. CLORO LIQUIDO OZZ 5.5% CANECA 20 KG (SKU: QUI0023) - 1 unidad - $11.99
2. CONTENEDOR DE COMIDA 8 1/2 PAQ X 25 UNDS (SKU: COM5293) - 10 unidades - $32.00
3. ESPONJA SALVAUNAS MIXTA UNIDAD (SKU: COM5083) - 24 unidades - $14.16
4. FUNDA PARA DESECHOS 18X20X1 BLANCA PAQ X 10UND (SKU: COM5256) - 10 unidades - $3.10
5. GUANTE PLASTICO TRANSPARENTE PARA COMIDA PAQ X 100 UNDS (SKU: COM5296) - 5 unidades - $4.55
6. GUANTE DE NITRILO NEGRO 5.5 TALLA L (SKU: COM5489) - 5 unidades - $31.50
7. SORBETE FLEXIBLE PAQ X100UNDS (SKU: COM5297) - 4 unidades - $3.24

---

**¡Con esta información puedes crear una integración completa entre WooCommerce y tu sistema SAP!** 🚀
