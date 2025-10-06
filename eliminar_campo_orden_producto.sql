-- Script para eliminar la columna orden_producto de la tabla pedido_items
-- Esta columna ya no se usa y está causando errores de NOT NULL constraint

-- Verificar si la columna existe antes de eliminarla
DO $$
BEGIN
    -- Verificar si la columna orden_producto existe
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'pedido_items' 
        AND column_name = 'orden_producto'
    ) THEN
        -- Eliminar la columna
        ALTER TABLE pedido_items DROP COLUMN orden_producto;
        RAISE NOTICE 'Columna orden_producto eliminada exitosamente de la tabla pedido_items';
    ELSE
        RAISE NOTICE 'La columna orden_producto no existe en la tabla pedido_items';
    END IF;
END $$;

-- Verificar la estructura actual de la tabla pedido_items
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'pedido_items' 
ORDER BY ordinal_position;
