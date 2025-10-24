-- Crear tabla para rastrear correos procesados y evitar duplicados
CREATE TABLE IF NOT EXISTS correos_procesados (
    id SERIAL PRIMARY KEY,
    uid_correo BIGINT NOT NULL UNIQUE,
    remitente VARCHAR(255) NOT NULL,
    asunto TEXT,
    fecha_correo TIMESTAMP,
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pedido_id INTEGER,
    estado_procesamiento VARCHAR(50) DEFAULT 'procesado',
    archivo_pdf VARCHAR(255),
    CONSTRAINT fk_correos_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- Crear índice para búsquedas rápidas por UID
CREATE INDEX IF NOT EXISTS idx_correos_uid ON correos_procesados(uid_correo);

-- Crear índice para búsquedas por fecha
CREATE INDEX IF NOT EXISTS idx_correos_fecha ON correos_procesados(fecha_procesamiento);
