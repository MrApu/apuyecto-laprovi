CREATE TABLE IF NOT EXISTS locales (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);

INSERT OR IGNORE INTO locales (id, nombre, activo) VALUES 
('restaurante', 'LA PROVINCIAL RESTAURANTE', 1),
('fast_food', 'LA PROVINCIAL FAST FOOD', 1);

CREATE TABLE IF NOT EXISTS policias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    apellidos TEXT NOT NULL,
    nombres TEXT NOT NULL,
    sa_pnp TEXT,
    area TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    observaciones TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre_mes TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO', 'CERRADO')),
    precio_ticket_policial REAL NOT NULL DEFAULT 12.00,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(anio, mes)
);

CREATE TABLE IF NOT EXISTS policias_mes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes_id INTEGER NOT NULL,
    policia_id INTEGER NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    area_historica TEXT NOT NULL,
    estado_en_mes TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (estado_en_mes IN ('ACTIVO', 'INACTIVO')),
    FOREIGN KEY(mes_id) REFERENCES meses(id) ON DELETE CASCADE,
    FOREIGN KEY(policia_id) REFERENCES policias(id) ON DELETE RESTRICT,
    UNIQUE(mes_id, policia_id, local_id)
);

CREATE TABLE IF NOT EXISTS tickets_por_policia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes_id INTEGER NOT NULL,
    policia_id INTEGER NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    dia INTEGER NOT NULL CHECK (dia BETWEEN 1 AND 31),
    valor INTEGER NOT NULL DEFAULT 1 CHECK (valor IN (0, 1)),
    fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mes_id) REFERENCES meses(id) ON DELETE CASCADE,
    FOREIGN KEY(policia_id) REFERENCES policias(id) ON DELETE RESTRICT,
    UNIQUE(mes_id, policia_id, local_id, dia)
);

CREATE TABLE IF NOT EXISTS tickets_diarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    dia_semana TEXT NOT NULL,
    para_unidad INTEGER NOT NULL DEFAULT 0 CHECK (para_unidad >= 0),
    local INTEGER NOT NULL DEFAULT 0 CHECK (local >= 0),
    total_policias INTEGER NOT NULL DEFAULT 0 CHECK (total_policias >= 0),
    vales_policiales INTEGER NOT NULL DEFAULT 0 CHECK (vales_policiales >= 0),
    observacion TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, local_id)
);

CREATE TABLE IF NOT EXISTS vales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    vales_entregados INTEGER NOT NULL DEFAULT 0 CHECK (vales_entregados >= 0),
    vales_consumidos INTEGER NOT NULL DEFAULT 0 CHECK (vales_consumidos >= 0),
    saldo INTEGER NOT NULL DEFAULT 0,
    observacion TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, local_id)
);

CREATE TABLE IF NOT EXISTS fast_food_consumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL UNIQUE,
    tickets_local INTEGER NOT NULL DEFAULT 0 CHECK (tickets_local >= 0),
    vales_local INTEGER NOT NULL DEFAULT 0 CHECK (vales_local >= 0),
    total_consumido INTEGER NOT NULL DEFAULT 0 CHECK (total_consumido >= 0),
    observacion TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pagos_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    total_tickets INTEGER NOT NULL DEFAULT 0 CHECK (total_tickets >= 0),
    tickets_pagados INTEGER NOT NULL DEFAULT 0 CHECK (tickets_pagados >= 0),
    tickets_debidos INTEGER NOT NULL DEFAULT 0 CHECK (tickets_debidos >= 0),
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PAGADO', 'PENDIENTE', 'PARCIAL')),
    monto_pagado REAL NOT NULL DEFAULT 0.0 CHECK (monto_pagado >= 0),
    monto_pendiente REAL NOT NULL DEFAULT 0.0 CHECK (monto_pendiente >= 0),
    observacion TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, local_id)
);

CREATE TABLE IF NOT EXISTS ventas_diarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    efectivo REAL NOT NULL DEFAULT 0.0 CHECK (efectivo >= 0),
    yape REAL NOT NULL DEFAULT 0.0 CHECK (yape >= 0),
    venta_sin_tickets REAL NOT NULL DEFAULT 0.0 CHECK (venta_sin_tickets >= 0),
    cantidad_tickets INTEGER NOT NULL DEFAULT 0 CHECK (cantidad_tickets >= 0),
    precio_ticket_aplicado REAL NOT NULL DEFAULT 12.00 CHECK (precio_ticket_aplicado > 0),
    venta_tickets REAL NOT NULL DEFAULT 0.0 CHECK (venta_tickets >= 0),
    venta_total REAL NOT NULL DEFAULT 0.0 CHECK (venta_total >= 0),
    venta_incluye_tickets INTEGER NOT NULL DEFAULT 0 CHECK (venta_incluye_tickets IN (0, 1)),
    para_unidad INTEGER NOT NULL DEFAULT 0,
    local INTEGER NOT NULL DEFAULT 0,
    vales_consumidos INTEGER NOT NULL DEFAULT 0,
    tickets_pagados INTEGER NOT NULL DEFAULT 0,
    tickets_debidos INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, local_id)
);

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    proveedor TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'INSUMOS',
    descripcion TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 1.0 CHECK (cantidad > 0),
    precio_unitario REAL NOT NULL DEFAULT 0.0 CHECK (precio_unitario >= 0),
    total REAL NOT NULL DEFAULT 0.0 CHECK (total >= 0),
    medio_pago TEXT NOT NULL DEFAULT 'EFECTIVO',
    nro_documento TEXT,
    observacion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    categoria TEXT NOT NULL DEFAULT 'SERVICIOS',
    descripcion TEXT NOT NULL,
    monto REAL NOT NULL DEFAULT 0.0 CHECK (monto >= 0),
    medio_pago TEXT NOT NULL DEFAULT 'EFECTIVO',
    observacion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pagos_personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    trabajador TEXT NOT NULL,
    cargo TEXT NOT NULL,
    concepto TEXT NOT NULL DEFAULT 'SUELDO',
    monto REAL NOT NULL DEFAULT 0.0 CHECK (monto >= 0),
    medio_pago TEXT NOT NULL DEFAULT 'EFECTIVO',
    observacion TEXT,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS observaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    local_id TEXT NOT NULL DEFAULT 'restaurante',
    texto TEXT NOT NULL,
    tipo TEXT DEFAULT 'GENERAL',
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS configuracion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    tipo_dato TEXT NOT NULL DEFAULT 'STRING',
    descripcion TEXT,
    fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS configuracion_historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT NOT NULL,
    fecha_cambio TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario TEXT DEFAULT 'SISTEMA',
    motivo TEXT
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario TEXT DEFAULT 'USUARIO',
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id TEXT,
    local_id TEXT,
    detalles TEXT
);

CREATE INDEX IF NOT EXISTS idx_policias_codigo ON policias(codigo);
CREATE INDEX IF NOT EXISTS idx_policias_area ON policias(area);
CREATE INDEX IF NOT EXISTS idx_meses_anio_mes ON meses(anio, mes);
CREATE INDEX IF NOT EXISTS idx_tickets_diarios_fecha_local ON tickets_diarios(fecha, local_id);
CREATE INDEX IF NOT EXISTS idx_ventas_diarias_fecha_local ON ventas_diarias(fecha, local_id);
CREATE INDEX IF NOT EXISTS idx_compras_fecha_local ON compras(fecha, local_id);
CREATE INDEX IF NOT EXISTS idx_gastos_fecha_local ON gastos(fecha, local_id);
CREATE INDEX IF NOT EXISTS idx_pagos_personal_fecha_local ON pagos_personal(fecha, local_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha);
