-- Script para crear la nueva tabla producto_alias con alias ilimitados
-- Este script también migra los datos de la tabla antigua alias_productos

-- Crear nueva tabla para alias ilimitados
CREATE TABLE IF NOT EXISTS producto_alias (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cliente_id, producto_id, alias)
);

-- Crear índices para mejorar el rendimiento de las búsquedas
CREATE INDEX IF NOT EXISTS idx_producto_alias_producto_id ON producto_alias(producto_id);
CREATE INDEX IF NOT EXISTS idx_producto_alias_cliente_id ON producto_alias(cliente_id);
CREATE INDEX IF NOT EXISTS idx_producto_alias_alias ON producto_alias(alias);
CREATE INDEX IF NOT EXISTS idx_producto_alias_cliente_producto ON producto_alias(cliente_id, producto_id);

-- Migrar datos de la tabla antigua alias_productos a la nueva producto_alias
-- Solo migrar alias que no estén vacíos
INSERT INTO producto_alias (producto_id, cliente_id, alias, fecha_creacion, fecha_actualizacion)
SELECT 
    producto_id, 
    cliente_id, 
    alias_1,
    fecha_creacion,
    fecha_actualizacion
FROM alias_productos 
WHERE alias_1 IS NOT NULL AND TRIM(alias_1) != ''
ON CONFLICT (cliente_id, producto_id, alias) DO NOTHING;

INSERT INTO producto_alias (producto_id, cliente_id, alias, fecha_creacion, fecha_actualizacion)
SELECT 
    producto_id, 
    cliente_id, 
    alias_2,
    fecha_creacion,
    fecha_actualizacion
FROM alias_productos 
WHERE alias_2 IS NOT NULL AND TRIM(alias_2) != ''
ON CONFLICT (cliente_id, producto_id, alias) DO NOTHING;

INSERT INTO producto_alias (producto_id, cliente_id, alias, fecha_creacion, fecha_actualizacion)
SELECT 
    producto_id, 
    cliente_id, 
    alias_3,
    fecha_creacion,
    fecha_actualizacion
FROM alias_productos 
WHERE alias_3 IS NOT NULL AND TRIM(alias_3) != ''
ON CONFLICT (cliente_id, producto_id, alias) DO NOTHING;

-- Eliminar la columna cantidad_alias_producto de la tabla clientes (ya no se necesita)
ALTER TABLE clientes DROP COLUMN IF EXISTS cantidad_alias_producto;

-- La tabla antigua alias_productos puede mantenerse por ahora como respaldo
-- Si desea eliminarla después de verificar que todo funciona bien, ejecute:
-- DROP TABLE IF EXISTS alias_productos;

-- Comentario: La tabla antigua alias_productos se mantiene como respaldo
-- Puede eliminarse manualmente una vez que se verifique que la migración fue exitosa

