# Instrucciones: Agregar Campo Ciudad a las Sucursales

## ✅ Cambios Realizados

Se ha agregado exitosamente el campo **"Ciudad"** a las sucursales en todo el sistema UnilimpioSur SAP. Este campo ahora está disponible en:

1. **Base de datos PostgreSQL** - Nueva columna `ciudad` en la tabla `sucursales`
2. **Interfaz web** - Nueva columna "Ciudad" visible en el cuadro de sucursales
3. **Modo de edición** - Se puede modificar el campo ciudad en modo edición
4. **Carga masiva** - Se puede subir el campo ciudad a través de archivos CSV o Excel

---

## 📋 Archivos Modificados

### 1. **agregar_campo_ciudad.sql** (NUEVO)
Script SQL para agregar la columna `ciudad` a la tabla `sucursales` en PostgreSQL.

### 2. **main.py**
- Actualizado endpoint `/api/clientes_con_sucursales` para incluir campo `ciudad`
- Actualizado endpoint `/api/sucursales/bulk` para guardar campo `ciudad`
- Actualizado endpoint `/api/sucursales/cliente/<int:cliente_id>` para incluir campo `ciudad`

### 3. **subir_datos.py**
- Actualizada función `_estandarizar_columnas_sucursales()` para reconocer columnas: "ciudad", "city", "localidad"
- Actualizada función `_upsert_sucursal()` para insertar el campo `ciudad`

### 4. **templates/clientes.html**
- Agregada columna "Ciudad" en el encabezado de la tabla de sucursales
- Actualizada función `agregarFilaVacia()` para incluir celda ciudad editable
- Actualizada función `construirFilaSucursal()` para mostrar el campo ciudad
- Actualizada función `construirTarjetaCliente()` para incluir header "Ciudad"
- Actualizada función `activarEdicionUI()` para permitir editar ciudad
- Actualizada función `recolectarCambios()` para recopilar el campo ciudad
- Actualizado mensaje de ayuda en modal "Subir datos de sucursales"

---

## 🚀 Instrucciones de Instalación

### Paso 1: Ejecutar Script SQL en PostgreSQL

Debe ejecutar el script SQL para agregar la columna `ciudad` a la tabla `sucursales`:

```bash
# Opción 1: Ejecutar desde terminal
psql -U postgres -d unilimpiosur_sap -f agregar_campo_ciudad.sql

# Opción 2: Ejecutar desde psql interactivo
psql -U postgres
\c unilimpiosur_sap
\i agregar_campo_ciudad.sql
```

### Paso 2: Reiniciar la Aplicación

Después de ejecutar el script SQL, reinicie el servidor Flask para que los cambios surtan efecto:

```bash
# Detener el servidor (Ctrl+C si está corriendo)
# Luego iniciar nuevamente
python main.py
```

---

## 📝 Uso del Campo Ciudad

### En la Interfaz Web

1. **Visualizar**: La columna "Ciudad" aparece automáticamente en todas las tablas de sucursales
2. **Editar**: 
   - Active el modo edición con el toggle "Habilitar edición"
   - Haga clic en la celda de "Ciudad" para editarla
   - Guarde los cambios con el botón "💾 Guardar Cambios"
3. **Agregar nuevas sucursales**: El campo ciudad está disponible en la fila de nueva sucursal

### Al Subir Archivos CSV/Excel

Cuando suba archivos CSV o Excel de sucursales, ahora puede incluir una columna con el nombre:
- `Ciudad`
- `ciudad`
- `city`
- `localidad`

**Ejemplo de archivo CSV:**
```csv
SAP,Alias,Encargado,Direccion,Telefono,Bodega,RUC,Ciudad
01,SUCURSAL NORTE,Juan Pérez,Av. Principal 123,02-2345678,10,1234567890001,Quito
02,SUCURSAL SUR,María López,Calle Secundaria 456,07-2345678,20,1234567890001,Cuenca
03,SUCURSAL COSTA,Pedro García,Av. del Mar 789,04-2345678,30,1234567890001,Guayaquil
```

**Nota**: El campo `Ciudad` es **opcional**. Si no se proporciona, se guardará como vacío (NULL).

---

## ✨ Características Adicionales

- ✅ Compatible con todas las modalidades de clientes (bodega por cliente o por sucursal)
- ✅ Compatible con clientes que usan alias por sucursal
- ✅ Compatible con clientes que usan RUC por sucursal
- ✅ Se puede buscar por ciudad usando la barra de búsqueda rápida
- ✅ Se valida automáticamente al guardar
- ✅ Soporta múltiples formatos de nombre de columna en CSV/Excel

---

## 🔍 Verificación

Para verificar que todo funciona correctamente:

1. **Base de datos**: Ejecute en PostgreSQL:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'sucursales' AND column_name = 'ciudad';
   ```
   
2. **Interfaz web**: 
   - Abra la página de Clientes (`http://localhost:5000/clientes`)
   - Verifique que aparece la columna "Ciudad" en las tablas de sucursales
   
3. **Modo edición**:
   - Active el modo edición
   - Edite el campo ciudad de una sucursal existente
   - Guarde los cambios
   - Recargue la página y verifique que se guardó correctamente

4. **Carga masiva**:
   - Prepare un archivo CSV con columna "Ciudad"
   - Suba el archivo desde el botón "📤 Subir Sucursales"
   - Verifique que las ciudades se cargaron correctamente

---

## 📞 Soporte

Si encuentra algún problema durante la instalación o uso del campo ciudad, revise:

1. Que el script SQL se ejecutó correctamente
2. Que reinició el servidor Flask después de ejecutar el script
3. Que no hay errores en la consola del navegador (F12 > Console)
4. Que no hay errores en los logs del servidor Flask

---

## 📅 Fecha de Implementación

**Octubre 4, 2025**

---

**¡Listo para usar! 🎉**

