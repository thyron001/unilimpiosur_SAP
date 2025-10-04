# Cambios en el Comentario del Archivo SAP

## 📋 Resumen de Cambios

Se ha modificado la generación del campo **Comments** en el archivo ODRF.txt para incluir información completa del pedido en el siguiente formato:

**Formato del Comentario:**
```
[Código SAP] | [URBANO (si ciudad ≠ Cuenca)] | Orden de compra: [Número] | Encargado: [Nombre]
```

**Separador:** Todos los campos están separados por ` | ` (pipe con espacios)

---

## 🔍 Detalles del Formato

### 1. **Código SAP** (Obligatorio)
- Es el código de almacén/bodega de la sucursal
- Se obtiene del campo `bodega` de la sucursal o `almacen`
- **Ejemplo:** `5`, `10`, `20`

### 2. **"URBANO"** (Condicional)
- Se incluye **SOLO** si la ciudad de la sucursal **NO es "Cuenca"**
- Siempre en mayúsculas: `URBANO`
- Si la ciudad es "Cuenca", este campo se omite
- **Ejemplo:** 
  - Ciudad = "Quito" → Se incluye "URBANO"
  - Ciudad = "Guayaquil" → Se incluye "URBANO"
  - Ciudad = "Cuenca" → NO se incluye

### 3. **Número de Orden de Compra** (Opcional)
- Se obtiene del campo `orden_compra` del pedido
- Se incluye solo si está disponible en el PDF procesado
- **Formato:** `Orden de compra: [número]`
- **Ejemplo:** `Orden de compra: OS-0-0-4887`

### 4. **Nombre del Encargado** (Opcional)
- Se obtiene del campo `encargado` de la sucursal
- Se incluye solo si está disponible
- **Formato:** `Encargado: [nombre]`
- **Ejemplo:** `Encargado: Gabriel Parra`, `Encargado: Juan Pérez`

---

## 📝 Ejemplos de Comentarios Generados

### Ejemplo 1: Pedido de Quito con todos los datos
```
Ciudad: Quito
Código SAP: 10
Orden de Compra: OS-0-0-4887
Encargado: Gabriel Parra

Comentario generado: "10 | URBANO | Orden de compra: OS-0-0-4887 | Encargado: Gabriel Parra"
```

### Ejemplo 2: Pedido de Cuenca con todos los datos
```
Ciudad: Cuenca
Código SAP: 20
Orden de Compra: OS-0-0-5123
Encargado: María López

Comentario generado: "20 | Orden de compra: OS-0-0-5123 | Encargado: María López"
```
*(Nota: NO incluye "URBANO" porque la ciudad es Cuenca)*

### Ejemplo 3: Pedido de Guayaquil sin orden de compra
```
Ciudad: Guayaquil
Código SAP: 30
Orden de Compra: (no disponible)
Encargado: Pedro García

Comentario generado: "30 | URBANO | Encargado: Pedro García"
```

### Ejemplo 4: Pedido con datos mínimos
```
Ciudad: (no disponible)
Código SAP: 5
Orden de Compra: (no disponible)
Encargado: (no disponible)

Comentario generado: "5"
```

---

## 🔧 Archivos Modificados

### **generador_sap.py**

Se modificaron las siguientes funciones:

1. **`obtener_pedidos_por_procesar()`**
   - Agregados campos: `s.ciudad`, `p.orden_compra`, `s.encargado`
   - Ahora recupera la información completa necesaria para generar el comentario

2. **`obtener_pedidos_por_ids()`**
   - Agregados campos: `s.ciudad`, `p.orden_compra`, `s.encargado`
   - Mantiene consistencia con la función anterior

3. **`generar_archivo_odrf()`**
   - Nueva lógica para generar el comentario con el formato requerido
   - Validaciones para cada campo antes de incluirlo
   - Comparación case-insensitive para la ciudad ("CUENCA")

---

## ✅ Validaciones Implementadas

El sistema valida automáticamente:

1. **Código SAP:** Siempre se incluye (usa valor por defecto "5" si no está disponible)
2. **Ciudad:** Se normaliza a mayúsculas para comparación
3. **Orden de Compra:** Se incluye solo si no está vacía
4. **Encargado:** Se incluye solo si no está vacío
5. **Espacios:** Los campos se unen con un espacio entre ellos

---

## 🚀 Uso

No se requieren cambios en el uso del sistema. Los comentarios se generarán automáticamente cuando:

1. Se hace clic en el botón **"Generar SAP"** en la interfaz web
2. Se ejecuta el script `generador_sap.py` directamente

### Desde la Interfaz Web:
1. Ir a la página de pedidos
2. Seleccionar los pedidos "Por Procesar"
3. Hacer clic en **"Generar SAP"**
4. Los archivos ODRF.txt y DRF1.txt se generarán con los nuevos comentarios

### Desde Terminal:
```bash
python generador_sap.py
```

---

## 🔍 Verificación

Para verificar que los comentarios se generan correctamente:

1. **Procesar un PDF con pedido de Quito:**
   - El comentario debe incluir "URBANO"
   
2. **Procesar un PDF con pedido de Cuenca:**
   - El comentario NO debe incluir "URBANO"
   
3. **Verificar campos opcionales:**
   - Si el PDF tiene orden de compra, debe aparecer en el comentario
   - Si la sucursal tiene encargado, debe aparecer en el comentario

4. **Revisar archivo ODRF.txt generado:**
   - Abrir el archivo con un editor de texto
   - Buscar la columna "Comments" (última columna)
   - Verificar el formato del comentario

---

## 📊 Estructura del Campo Comments en ODRF.txt

El archivo ODRF.txt tiene la siguiente estructura (últimas columnas):

```
... | ShipToCode | U_EXX_ALMACEN | Comments
... | MATRIZ     | 10            | 10 | URBANO | Orden de compra: OS-0-0-4887 | Encargado: Gabriel Parra
```

---

## 🎯 Beneficios

1. **Trazabilidad completa:** Toda la información del pedido en un solo campo
2. **Identificación rápida:** Saber si es envío urbano o no
3. **Referencia cruzada:** Número de orden de compra para auditoría
4. **Responsabilidad:** Nombre del encargado asociado al pedido
5. **Flexibilidad:** Campos opcionales que se adaptan a la información disponible

---

## 📅 Fecha de Implementación

**Octubre 4, 2025**

---

## ⚠️ Notas Importantes

1. **El campo ciudad debe estar lleno:** Para que funcione correctamente la lógica de "URBANO", asegúrese de que las sucursales tengan el campo `ciudad` completo en la base de datos.

2. **Orden de compra del PDF:** La orden de compra se extrae automáticamente del PDF. Si no se detecta, el comentario se generará sin ese campo.

3. **Encargado de la sucursal:** Debe estar registrado en la base de datos en la tabla `sucursales`.

4. **Comparación de ciudad:** La comparación con "Cuenca" es case-insensitive (no distingue mayúsculas/minúsculas), por lo que "CUENCA", "Cuenca", "cuenca" se tratarán igual.

---

**¡Listo para usar! 🎉**

