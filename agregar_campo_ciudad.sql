-- Script para agregar campo ciudad a la tabla sucursales
-- Sistema UnilimpioSur SAP - PostgreSQL
-- 
-- INSTRUCCIONES:
-- 1. Conectarse a la base de datos unilimpiosur_sap
-- 2. Ejecutar este script
--
-- Nota: Este script verifica si la columna ya existe antes de agregarla

\c unilimpiosur_sap;

-- Agregar columna ciudad a la tabla sucursales (si no existe)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sucursales' 
        AND column_name = 'ciudad'
    ) THEN
        ALTER TABLE sucursales 
        ADD COLUMN ciudad TEXT;
        
        RAISE NOTICE 'Columna "ciudad" agregada exitosamente a la tabla sucursales';
    ELSE
        RAISE NOTICE 'La columna "ciudad" ya existe en la tabla sucursales';
    END IF;
END $$;

-- Verificar que la columna se agregó correctamente
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sucursales'
AND column_name = 'ciudad';

COMMIT;

