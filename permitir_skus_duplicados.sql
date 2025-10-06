-- =====================================================
-- SCRIPT PARA PERMITIR SKUs DUPLICADOS CON DIFERENTES ALIAS
-- Sistema UnilimpioSur SAP - PostgreSQL
-- =====================================================
-- 
-- Este script modifica la base de datos para permitir
-- SKUs duplicados con diferentes alias, cambiando la
-- gestión de productos para que se base en ID en lugar de SKU.
-- 
-- INSTRUCCIONES DE USO:
-- 1. Conectarse a PostgreSQL como superusuario
-- 2. Ejecutar este script completo
-- 3. Reiniciar la aplicación
-- 
-- =====================================================

-- Conectar a la base de datos
\c unilimpiosur_sap;

-- =====================================================
-- 1. ELIMINAR RESTRICCIÓN DE UNICIDAD EN SKU
-- =====================================================

-- Eliminar la restricción de unicidad en SKU
ALTER TABLE productos DROP CONSTRAINT IF EXISTS uq_productos_sku;

-- =====================================================
-- 2. CREAR TABLA DE ALIAS DE PRODUCTOS (si no existe)
-- =====================================================

CREATE TABLE IF NOT EXISTS alias_productos (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    alias_1 TEXT,
    alias_2 TEXT,
    alias_3 TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Un producto puede tener múltiples alias por cliente
    CONSTRAINT uq_alias_productos_cliente_producto UNIQUE (cliente_id, producto_id)
);

-- Índices para alias_productos
CREATE INDEX IF NOT EXISTS idx_alias_productos_cliente ON alias_productos (cliente_id);
CREATE INDEX IF NOT EXISTS idx_alias_productos_producto ON alias_productos (producto_id);

-- =====================================================
-- 3. AGREGAR COLUMNAS DE CONFIGURACIÓN A CLIENTES (si no existen)
-- =====================================================

-- Agregar columnas para manejo de alias si no existen
DO $$
BEGIN
    -- Verificar si la columna existe antes de agregarla
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'alias_por_sucursal') THEN
        ALTER TABLE clientes ADD COLUMN alias_por_sucursal BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'alias_por_producto') THEN
        ALTER TABLE clientes ADD COLUMN alias_por_producto BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'cantidad_alias_producto') THEN
        ALTER TABLE clientes ADD COLUMN cantidad_alias_producto INT NOT NULL DEFAULT 1;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'clientes' AND column_name = 'ruc_por_sucursal') THEN
        ALTER TABLE clientes ADD COLUMN ruc_por_sucursal BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- =====================================================
-- 4. AGREGAR COLUMNAS A SUCURSALES (si no existen)
-- =====================================================

DO $$
BEGIN
    -- Verificar si las columnas existen antes de agregarlas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'sucursales' AND column_name = 'ruc') THEN
        ALTER TABLE sucursales ADD COLUMN ruc VARCHAR(13);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'sucursales' AND column_name = 'ciudad') THEN
        ALTER TABLE sucursales ADD COLUMN ciudad TEXT;
    END IF;
END $$;

-- =====================================================
-- 5. CREAR ÍNDICES ADICIONALES PARA MEJORAR RENDIMIENTO
-- =====================================================

-- Índice para buscar productos por SKU (ahora que puede haber duplicados)
CREATE INDEX IF NOT EXISTS idx_productos_sku ON productos (sku);

-- Índice para buscar productos por nombre (case insensitive)
CREATE INDEX IF NOT EXISTS idx_productos_nombre_ci ON productos (upper(nombre));

-- =====================================================
-- 6. COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE productos IS 'Catálogo de productos. Ahora permite SKUs duplicados con diferentes alias.';
COMMENT ON TABLE alias_productos IS 'Alias de productos por cliente. Permite múltiples nombres para el mismo producto.';
COMMENT ON COLUMN productos.sku IS 'Código SKU del producto. Puede estar duplicado para diferentes variaciones.';
COMMENT ON COLUMN alias_productos.alias_1 IS 'Primer alias del producto para este cliente';
COMMENT ON COLUMN alias_productos.alias_2 IS 'Segundo alias del producto para este cliente';
COMMENT ON COLUMN alias_productos.alias_3 IS 'Tercer alias del producto para este cliente';

-- =====================================================
-- 7. MOSTRAR RESUMEN DE CAMBIOS
-- =====================================================

SELECT 
    'Cambios aplicados exitosamente' as mensaje,
    'SKUs duplicados ahora permitidos' as cambio_principal,
    current_database() as base_datos,
    current_user as usuario;

-- Mostrar estructura actualizada de la tabla productos
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'productos' 
ORDER BY ordinal_position;

-- Mostrar estructura de la tabla alias_productos
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'alias_productos' 
ORDER BY ordinal_position;

COMMIT;
