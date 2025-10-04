-- =====================================================
-- Script para eliminar campo bodega de sucursales
-- =====================================================
-- Este script elimina la columna 'bodega' de la tabla sucursales
-- ya que se determinó que no es necesaria en la asignación de sucursales.
-- 
-- NOTA: Esto NO afecta las tablas de bodega de productos
--       (bodegas_producto_por_cliente y bodegas_producto_por_sucursal)
--       que permanecen intactas.
-- =====================================================

-- Conectar a la base de datos (ajustar según sea necesario)
-- \c unilimpiosur_sap;

-- Eliminar columna bodega de la tabla sucursales
ALTER TABLE sucursales DROP COLUMN IF EXISTS bodega;

-- Verificar que la columna fue eliminada
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'sucursales' 
ORDER BY ordinal_position;

-- Mensaje de confirmación
SELECT 'Columna bodega eliminada exitosamente de la tabla sucursales' as mensaje;

COMMIT;

