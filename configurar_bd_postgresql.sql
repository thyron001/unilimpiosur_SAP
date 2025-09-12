-- =====================================================
-- SCRIPT DE CONFIGURACIÓN COMPLETA DE BASE DE DATOS
-- Sistema UnilimpioSur SAP - PostgreSQL
-- =====================================================
-- 
-- Este script configura completamente la base de datos
-- para el sistema de gestión de pedidos UnilimpioSur.
-- 
-- INSTRUCCIONES DE USO:
-- 1. Conectarse a PostgreSQL como superusuario
-- 2. Ejecutar este script completo
-- 3. Configurar las variables de entorno en el VPS
-- 
-- =====================================================

-- Crear base de datos
-- =====================================================
CREATE DATABASE unilimpiosur_sap
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_ES.UTF-8'
    LC_CTYPE = 'es_ES.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Conectar a la base de datos creada
\c unilimpiosur_sap;

-- =====================================================
-- 1. TABLA DE CONFIGURACIÓN DEL SISTEMA
-- =====================================================
CREATE TABLE IF NOT EXISTS configuracion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) NOT NULL UNIQUE,
    valor TEXT,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuración inicial
INSERT INTO configuracion (clave, valor, descripcion) VALUES
('numero_pedido_inicial', '10000', 'Número inicial para asignar a los pedidos nuevos')
ON CONFLICT (clave) DO NOTHING;

-- =====================================================
-- 2. TABLA DE CLIENTES
-- =====================================================
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    ruc VARCHAR(13) NOT NULL,
    -- Si TRUE, este cliente maneja bodega por sucursal (segunda categoría)
    usa_bodega_por_sucursal BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_clientes_ruc UNIQUE (ruc)
);

-- Unicidad de nombre (insensible a mayúsculas/minúsculas)
CREATE UNIQUE INDEX IF NOT EXISTS uq_clientes_nombre_ci 
ON clientes (upper(nombre));

-- =====================================================
-- 3. TABLA DE SUCURSALES (por cliente)
-- =====================================================
CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    alias TEXT, -- alias que llega en PDF (opcional)
    nombre TEXT NOT NULL, -- nombre "oficial" que usa el sistema
    encargado TEXT,
    direccion TEXT,
    telefono TEXT,
    almacen VARCHAR(10), -- número de almacén para SAP
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unicidad de nombre por cliente (insensible a mayúsculas/minúsculas)
CREATE UNIQUE INDEX IF NOT EXISTS uq_sucursales_cliente_nombre_ci 
ON sucursales (cliente_id, upper(nombre));

CREATE INDEX IF NOT EXISTS idx_sucursales_cliente 
ON sucursales (cliente_id);

-- =====================================================
-- 4. TABLA DE PRODUCTOS (catálogo)
-- =====================================================
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    nombre TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_productos_sku UNIQUE (sku)
);

-- =====================================================
-- 5. TABLA DE BODEGA POR PRODUCTO Y CLIENTE
-- (primera categoría: por cliente)
-- =====================================================
CREATE TABLE IF NOT EXISTS bodegas_producto_por_cliente (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    bodega VARCHAR(50) NOT NULL,
    -- Un producto tiene una sola bodega para ese cliente
    CONSTRAINT uq_bod_cli UNIQUE (cliente_id, producto_id)
);

CREATE INDEX IF NOT EXISTS idx_bod_cli_cliente_prod 
ON bodegas_producto_por_cliente (cliente_id, producto_id);

-- =====================================================
-- 6. TABLA DE BODEGA POR PRODUCTO Y SUCURSAL
-- (segunda categoría: por sucursal + cliente)
-- =====================================================
CREATE TABLE IF NOT EXISTS bodegas_producto_por_sucursal (
    id SERIAL PRIMARY KEY,
    sucursal_id INT NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    bodega VARCHAR(50) NOT NULL,
    -- Un producto tiene una sola bodega para esa sucursal
    CONSTRAINT uq_bod_suc UNIQUE (sucursal_id, producto_id)
);

CREATE INDEX IF NOT EXISTS idx_bod_suc_sucursal_prod 
ON bodegas_producto_por_sucursal (sucursal_id, producto_id);

-- =====================================================
-- 7. TABLA DE PEDIDOS
-- =====================================================
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    numero_pedido INT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) NOT NULL,
    sucursal TEXT, -- mantiene el texto original del PDF
    subtotal_bruto NUMERIC(12,2), -- primer "Subtotal" (antes de descuento)
    descuento NUMERIC(12,2) DEFAULT 0, -- "Descuento"
    subtotal_neto NUMERIC(12,2), -- segundo "Subtotal" (después del descuento)
    iva_0 NUMERIC(12,2), -- "IVA 0%"
    iva_15 NUMERIC(12,2), -- "IVA 15%"
    estado VARCHAR(20) DEFAULT 'por_procesar', -- por_procesar, procesado, con_errores
    cliente_id INT REFERENCES clientes(id) ON DELETE SET NULL,
    sucursal_id INT REFERENCES sucursales(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para pedidos
CREATE INDEX IF NOT EXISTS idx_pedidos_numero ON pedidos (numero_pedido);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos (estado);
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON pedidos (fecha);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos (cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_sucursal ON pedidos (sucursal_id);

-- =====================================================
-- 8. TABLA DE ITEMS DE PEDIDOS
-- =====================================================
CREATE TABLE IF NOT EXISTS pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    sku VARCHAR(50),
    bodega VARCHAR(50),
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(12,2),
    precio_total NUMERIC(12,2),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para items de pedidos
CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido ON pedido_items (pedido_id);
CREATE INDEX IF NOT EXISTS idx_pedido_items_sku ON pedido_items (sku);

-- =====================================================
-- 9. DATOS INICIALES DE EJEMPLO
-- =====================================================

-- Insertar cliente de ejemplo (Roldan)
INSERT INTO clientes (nombre, ruc, usa_bodega_por_sucursal) VALUES
('COMERCIAL CARLOS ROLDAN CIA LTDA', '0991234567001', FALSE)
ON CONFLICT (ruc) DO NOTHING;

-- Obtener el ID del cliente Roldan
DO $$
DECLARE
    cliente_roldan_id INT;
BEGIN
    SELECT id INTO cliente_roldan_id FROM clientes WHERE ruc = '0991234567001';
    
    IF cliente_roldan_id IS NOT NULL THEN
        -- Insertar sucursales de ejemplo para Roldan
        INSERT INTO sucursales (cliente_id, nombre, direccion, telefono, almacen) VALUES
        (cliente_roldan_id, 'PATIO RIOBAMBA', 'Av. 10 de Agosto y Av. Unidad Nacional', '02-2345678', '01'),
        (cliente_roldan_id, 'SUCURSAL CUENCA', 'Calle Larga y Av. Solano', '07-2345678', '02'),
        (cliente_roldan_id, 'SUCURSAL GUAYAQUIL', 'Av. 9 de Octubre y Malecón', '04-2345678', '03')
        ON CONFLICT (cliente_id, upper(nombre)) DO NOTHING;
    END IF;
END $$;

-- =====================================================
-- 10. FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar fecha_actualizacion
CREATE OR REPLACE FUNCTION actualizar_fecha_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar fecha_actualizacion
CREATE TRIGGER trigger_actualizar_configuracion
    BEFORE UPDATE ON configuracion
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

CREATE TRIGGER trigger_actualizar_pedidos
    BEFORE UPDATE ON pedidos
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_modificacion();

-- =====================================================
-- 11. VISTAS ÚTILES
-- =====================================================

-- Vista para pedidos con información completa
CREATE OR REPLACE VIEW vista_pedidos_completa AS
SELECT 
    p.id,
    p.numero_pedido,
    p.fecha,
    p.total,
    p.sucursal as sucursal_texto,
    p.estado,
    c.nombre as cliente_nombre,
    c.ruc as cliente_ruc,
    s.nombre as sucursal_nombre,
    s.direccion as sucursal_direccion,
    s.telefono as sucursal_telefono,
    s.almacen as sucursal_almacen,
    p.subtotal_bruto,
    p.descuento,
    p.subtotal_neto,
    p.iva_0,
    p.iva_15
FROM pedidos p
LEFT JOIN clientes c ON p.cliente_id = c.id
LEFT JOIN sucursales s ON p.sucursal_id = s.id;

-- Vista para estadísticas de pedidos
CREATE OR REPLACE VIEW vista_estadisticas_pedidos AS
SELECT 
    estado,
    COUNT(*) as cantidad,
    SUM(total) as total_monto,
    AVG(total) as promedio_monto,
    MIN(fecha) as fecha_mas_antigua,
    MAX(fecha) as fecha_mas_reciente
FROM pedidos
GROUP BY estado;

-- =====================================================
-- 12. PERMISOS Y USUARIOS
-- =====================================================

-- Crear usuario específico para la aplicación
-- (Descomenta y ajusta según tus necesidades)
/*
CREATE USER unilimpiosur_app WITH PASSWORD 'tu_password_seguro_aqui';
GRANT CONNECT ON DATABASE unilimpiosur_sap TO unilimpiosur_app;
GRANT USAGE ON SCHEMA public TO unilimpiosur_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO unilimpiosur_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO unilimpiosur_app;
*/

-- =====================================================
-- 13. CONFIGURACIONES ADICIONALES
-- =====================================================

-- Configurar timezone
SET timezone = 'America/Guayaquil';

-- Configuraciones de rendimiento
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- =====================================================
-- FINALIZACIÓN
-- =====================================================

-- Mostrar resumen de la configuración
SELECT 
    'Base de datos configurada exitosamente' as mensaje,
    current_database() as base_datos,
    current_user as usuario,
    version() as version_postgresql;

-- Mostrar tablas creadas
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Mostrar configuración inicial
SELECT clave, valor, descripcion 
FROM configuracion 
ORDER BY clave;

COMMIT;
