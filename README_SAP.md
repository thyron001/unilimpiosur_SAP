# Sistema de Gestión de Pedidos SAP

## Funcionalidades Implementadas

### 1. Estados de Pedidos
- **Por procesar**: Pedidos recién recibidos que esperan ser procesados
- **Procesado**: Pedidos que ya han sido enviados a SAP
- **Con errores**: Pedidos que tuvieron problemas durante el procesamiento

### 2. Subpestañas en la Vista de Pedidos
- Navegación entre diferentes estados de pedidos
- Filtrado dinámico de pedidos por estado
- Indicador visual del estado actual

### 3. Generación de Archivos SAP
- **Botón flotante SAP**: Aparece solo en la subpestaña "Por procesar"
- Genera archivos `ODRF.txt` y `DRF1.txt` con formato SAP
- Actualiza automáticamente el estado de los pedidos a "procesado"

### 4. Estructura de Archivos SAP

#### ODRF.txt (Documentos)
```
DocEntry	DocNum	DocType	Printed	DocDate	DocDueDate	CardCode	ObjType	Series	ShipToCode	U_EXX_ALMACEN	Comments	UseShpdGd
```
- **DocEntry/DocNum**: Número del pedido
- **DocType**: Siempre "dDocument_Items"
- **Printed**: Siempre "Y"
- **DocDate/DocDueDate**: Fecha en formato YYYYMMDD
- **CardCode**: RUC del cliente en formato CLXXXXXXXXXXXXX
- **ObjType**: Siempre "17"
- **Series**: Siempre "13"
- **ShipToCode**: Nombre de la sucursal
- **U_EXX_ALMACEN**: Número del almacén de la sucursal
- **Comments**: Dirección y teléfono de la sucursal
- **UseShpdGd**: Siempre "N"

#### DRF1.txt (Líneas de Documento)
```
DocNum	ItemCode	Quantity	WhsCode	CogsOcrCo5	UseShpdGd
```
- **DocNum**: Número del pedido
- **ItemCode**: SKU del producto
- **Quantity**: Cantidad
- **WhsCode**: Número de bodega del producto
- **CogsOcrCo5**: Nombre de la sucursal
- **UseShpdGd**: Siempre "N"

## Modificaciones en la Base de Datos

### Tabla `pedidos`
- Agregada columna `estado` VARCHAR(20) con valores: 'por_procesar', 'procesado', 'con_errores'
- Valor por defecto: 'por_procesar'

### Tabla `sucursales`
- Agregada columna `almacen` VARCHAR(10) para el campo U_EXX_ALMACEN

## Uso del Sistema

### 1. Ver Pedidos por Estado
1. Navegar a `/pedidos`
2. Hacer clic en las subpestañas: "Por procesar", "Procesado", "Con errores"
3. Los pedidos se filtran automáticamente

### 2. Generar Archivos SAP
1. Ir a la subpestaña "Por procesar"
2. Hacer clic en el botón flotante "SAP" (esquina inferior derecha)
3. Confirmar la generación
4. Los archivos se generan con timestamp y los pedidos pasan a estado "procesado"

### 3. Configurar Almacenes de Sucursales
1. Ir a `/clientes`
2. Editar las sucursales y agregar el número de almacén en el campo correspondiente
3. Este valor se usará en el campo U_EXX_ALMACEN de los archivos SAP

## Archivos Generados

Los archivos SAP se generan en la carpeta del proyecto con el formato:
- `ODRF_YYYYMMDD_HHMMSS.txt`
- `DRF1_YYYYMMDD_HHMMSS.txt`

## APIs Disponibles

### GET `/api/pedidos/por_estado/<estado>`
Obtiene pedidos filtrados por estado.

### POST `/api/generar_sap`
Genera archivos SAP para todos los pedidos en estado "por_procesar".

## Notas Técnicas

- Los archivos se generan con separadores de tabulación
- Las fechas se formatean como YYYYMMDD
- Los RUC se formatean como CLXXXXXXXXXXXXX
- Los pedidos se marcan automáticamente como "procesado" después de generar los archivos
- El sistema mantiene la integridad referencial con las tablas de clientes y sucursales
