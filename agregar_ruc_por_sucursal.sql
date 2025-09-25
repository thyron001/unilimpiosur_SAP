-- =====================================================
-- SCRIPT PARA AGREGAR FUNCIONALIDAD RUC POR SUCURSAL
-- Sistema UnilimpioSur SAP
-- =====================================================
-- 
-- Este script agrega la funcionalidad para manejar RUC
-- por cliente o por sucursal según configuración.
-- 
-- =====================================================

-- 1. Agregar columna ruc_por_sucursal a tabla clientes
-- =====================================================
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS ruc_por_sucursal BOOLEAN NOT NULL DEFAULT FALSE;

-- Comentario para la columna
COMMENT ON COLUMN clientes.ruc_por_sucursal IS 'Si TRUE, cada sucursal tiene su propio RUC. Si FALSE, se usa el RUC del cliente para todas las sucursales.';

-- 2. Agregar columna ruc a tabla sucursales
-- =====================================================
ALTER TABLE sucursales 
ADD COLUMN IF NOT EXISTS ruc VARCHAR(13);

-- Comentario para la columna
COMMENT ON COLUMN sucursales.ruc IS 'RUC específico de la sucursal. Solo se usa si el cliente tiene ruc_por_sucursal = TRUE.';

-- 3. Crear índice para búsquedas por RUC de sucursal
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_sucursales_ruc 
ON sucursales (ruc) 
WHERE ruc IS NOT NULL;

-- 4. Agregar restricción de unicidad para RUC de sucursales
-- =====================================================
-- Solo permitir RUC únicos cuando no son NULL
CREATE UNIQUE INDEX IF NOT EXISTS uq_sucursales_ruc 
ON sucursales (ruc) 
WHERE ruc IS NOT NULL AND ruc != '';

-- 5. Actualizar datos existentes (opcional)
-- =====================================================
-- Si quieres que todos los clientes existentes usen RUC por cliente por defecto
-- (esto ya está cubierto por el DEFAULT FALSE en la columna)

-- 6. Mostrar resumen de cambios
-- =====================================================
SELECT 
    'Columnas agregadas exitosamente' as mensaje,
    'clientes.ruc_por_sucursal' as columna_cliente,
    'sucursales.ruc' as columna_sucursal;

-- Mostrar estructura actualizada
SELECT 
    'clientes' as tabla,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'clientes' 
AND column_name IN ('ruc', 'ruc_por_sucursal')
ORDER BY column_name;

SELECT 
    'sucursales' as tabla,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'sucursales' 
AND column_name = 'ruc'
ORDER BY column_name;

COMMIT;

