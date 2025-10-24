# Instrucciones de Migración: Sistema de Alias Ilimitados

## Resumen de Cambios

Se ha refactorizado completamente el sistema de gestión de alias de productos, cambiando de un sistema limitado a 3 alias por producto a un sistema de **alias ilimitados** gestionados a través de un modal interactivo.

## 📋 Pasos para Migrar

### 1. Ejecutar Script SQL de Migración

**IMPORTANTE**: Antes de ejecutar el script, haz un backup completo de tu base de datos.

```bash
# En PostgreSQL, ejecuta el siguiente comando:
psql -U tu_usuario -d nombre_base_datos -f crear_tabla_producto_alias.sql
```

Este script:
- ✅ Crea la nueva tabla `producto_alias` con alias ilimitados
- ✅ Crea índices para optimizar las búsquedas
- ✅ Migra automáticamente todos los alias existentes (alias_1, alias_2, alias_3) a la nueva tabla
- ✅ Elimina la columna `cantidad_alias_producto` de la tabla `clientes`
- ⚠️ Mantiene la tabla antigua `alias_productos` como respaldo (puedes eliminarla manualmente después de verificar que todo funciona correctamente)

### 2. Reiniciar la Aplicación

Una vez ejecutado el script SQL, reinicia tu aplicación Python para que use los nuevos cambios de código:

```bash
py main.py
```

## 🎯 Cambios Principales

### 1. Base de Datos
- **Nueva tabla**: `producto_alias` con estructura:
  - `id` (serial, PK)
  - `producto_id` (FK a productos)
  - `cliente_id` (FK a clientes)
  - `alias` (text) - UN alias por registro
  - `fecha_creacion` (timestamp)
  - `fecha_actualizacion` (timestamp)
  - Constraint único: `(cliente_id, producto_id, alias)`

### 2. Interfaz de Usuario

#### Sección de Clientes (`/clientes`)
- **ELIMINADO**: Campo "Cantidad de Alias por Producto"
- **ACTUALIZADO**: El checkbox "Activar Alias por Producto" ahora indica que los alias se gestionan desde la vista de productos

#### Sección de Productos (`/productos`)
- **ELIMINADO**: Columnas "Alias 1", "Alias 2", "Alias 3" de la tabla de productos
- **NUEVO**: Columna "Alias" con botón "📝 Alias" para productos de clientes con alias activados
- **NUEVO**: Modal de gestión de alias con:
  - Lista de todos los alias del producto
  - Capacidad de agregar alias ilimitados
  - Edición inline de alias existentes
  - Eliminación de alias

### 3. Procesamiento de Pedidos
- Actualizado para buscar en TODOS los alias de la nueva tabla `producto_alias`
- Funciona de manera transparente con alias ilimitados

### 4. Importación de Productos (CSV/XLSX)
- **ELIMINADO**: Soporte para columnas Alias1, Alias2, Alias3 en archivos de importación
- **NOTA**: Los alias ahora se gestionan ÚNICAMENTE desde el modal de alias en el frontend
- Mensaje informativo en el modal de importación para clientes con alias activados

## 🔄 Flujo de Trabajo Nuevo

### Para Gestionar Alias de un Producto:

1. Ve a la sección **Productos** (`/productos`)
2. Localiza el producto del cliente deseado
3. Haz clic en el botón **"📝 Alias"** en la fila del producto
4. En el modal que aparece:
   - **Agregar**: Escribe el alias en el campo y presiona "➕ Agregar" o Enter
   - **Editar**: Haz clic en "✏️" junto al alias, modifica el texto y guarda
   - **Eliminar**: Haz clic en "🗑️" para eliminar un alias (con confirmación)

### Búsqueda en Pedidos:

Cuando llegue un pedido con un nombre de producto:
1. El sistema primero busca por coincidencia exacta en el nombre del producto
2. Si no encuentra, busca en **TODOS** los alias del cliente
3. Funciona de manera transparente con cualquier cantidad de alias

## ⚠️ Consideraciones Importantes

### Datos Existentes
- ✅ Todos los alias existentes (alias_1, alias_2, alias_3) se migran automáticamente a la nueva tabla
- ✅ No se pierde ningún dato durante la migración
- ✅ La tabla antigua `alias_productos` se mantiene como respaldo

### Validaciones
- ✅ No se permiten alias duplicados para el mismo producto y cliente
- ✅ Los alias no pueden estar vacíos
- ✅ Constraint único en base de datos previene duplicados

### Rendimiento
- ✅ Índices creados en `producto_id`, `cliente_id`, `alias` y `(cliente_id, producto_id)`
- ✅ Las búsquedas son eficientes incluso con muchos alias

## 📁 Archivos Modificados

1. **crear_tabla_producto_alias.sql** - Script de migración de base de datos
2. **templates/clientes.html** - Eliminado campo cantidad de alias
3. **templates/productos.html** - Nueva UI con modal de gestión de alias
4. **main.py** - Nuevos endpoints API + actualización de endpoints existentes
5. **procesamiento_pedidos.py** - Búsqueda en nueva tabla de alias
6. **subir_datos.py** - Eliminada lógica de alias en importación

## 🧪 Verificación Post-Migración

Después de la migración, verifica:

1. ✅ Ejecuta el script SQL sin errores
2. ✅ La aplicación inicia correctamente
3. ✅ En `/clientes` ya no aparece el campo "Cantidad de Alias"
4. ✅ En `/productos` aparece el botón "📝 Alias" para clientes con alias activados
5. ✅ Al hacer clic en "📝 Alias" aparece el modal con los alias migrados
6. ✅ Puedes agregar, editar y eliminar alias desde el modal
7. ✅ Los pedidos se procesan correctamente usando los alias

## 🔒 Rollback (En Caso de Problemas)

Si necesitas revertir los cambios:

1. Restaura el backup de tu base de datos
2. Revierte los cambios de código usando Git:
   ```bash
   git checkout HEAD~1
   ```

## 📞 Soporte

Si encuentras algún problema durante la migración:
- Verifica los logs de la aplicación
- Verifica los logs de PostgreSQL
- Asegúrate de que todos los archivos se actualizaron correctamente

---

**Fecha de Migración**: Octubre 2025  
**Versión**: 2.0 - Sistema de Alias Ilimitados

