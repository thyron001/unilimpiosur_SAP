-- =====================================================
-- MODIFICACIÓN DE TABLA CLIENTES
-- Agregar columnas para configuración de alias
-- =====================================================

-- Conectar a la base de datos
\c pedidos;

-- Agregar nuevas columnas a la tabla clientes
ALTER TABLE clientes 
ADD COLUMN IF NOT EXISTS alias_por_sucursal BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS alias_por_producto BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS cantidad_alias_producto INTEGER DEFAULT 1 CHECK (cantidad_alias_producto >= 1 AND cantidad_alias_producto <= 3);

-- Actualizar clientes existentes con valores por defecto
UPDATE clientes 
SET 
    alias_por_sucursal = FALSE,
    alias_por_producto = FALSE,
    cantidad_alias_producto = 1
WHERE alias_por_sucursal IS NULL OR alias_por_producto IS NULL OR cantidad_alias_producto IS NULL;

-- Crear tabla para alias de productos por cliente
CREATE TABLE IF NOT EXISTS alias_productos (
    id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    alias_1 TEXT,
    alias_2 TEXT,
    alias_3 TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evitar duplicados para el mismo producto y cliente
CREATE UNIQUE INDEX IF NOT EXISTS uq_alias_prod_cliente 
ON alias_productos (cliente_id, producto_id);

CREATE INDEX IF NOT EXISTS idx_alias_productos_cliente 
ON alias_productos (cliente_id);

-- Trigger para actualizar fecha_actualizacion en alias_productos
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion_alias()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_alias_productos
    BEFORE UPDATE ON alias_productos
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion_alias();

-- Mostrar resumen de cambios
SELECT 
    'Tabla clientes modificada exitosamente' as mensaje,
    COUNT(*) as total_clientes
FROM clientes;

-- Mostrar estructura actualizada
\d clientes;
