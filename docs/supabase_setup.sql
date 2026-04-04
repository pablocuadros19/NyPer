-- ============================================================
-- NyPer — Tablas Supabase
-- Ejecutar en el SQL Editor de Supabase (dashboard > SQL Editor)
-- ============================================================

-- Key-value store para leads, config, sesiones
CREATE TABLE IF NOT EXISTS nyper_storage (
    key TEXT PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    email TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'usuario',
    color TEXT NOT NULL DEFAULT '#00A651',
    activo INTEGER NOT NULL DEFAULT 1,
    codigo_afiliado TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Ownership de prospectos
CREATE TABLE IF NOT EXISTS ownership (
    lead_id TEXT NOT NULL,
    sucursal_codigo TEXT NOT NULL,
    owner_email TEXT NOT NULL REFERENCES usuarios(email),
    fecha_toma TEXT NOT NULL,
    canal TEXT DEFAULT '',
    PRIMARY KEY (lead_id, sucursal_codigo)
);

-- Cartera personal de clientes
CREATE TABLE IF NOT EXISTS cartera (
    id BIGSERIAL PRIMARY KEY,
    owner_email TEXT NOT NULL REFERENCES usuarios(email),
    nombre_razon_social TEXT NOT NULL,
    cuit TEXT DEFAULT '',
    rubro TEXT DEFAULT '',
    subrubro TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    mail TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    localidad TEXT DEFAULT '',
    observaciones TEXT DEFAULT '',
    nivel_paquete TEXT DEFAULT '',
    criterios_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_cartera_owner ON cartera(owner_email);
CREATE INDEX IF NOT EXISTS idx_ownership_suc ON ownership(sucursal_codigo);

-- Habilitar RLS (Row Level Security) desactivado para simplificar
-- La app maneja permisos internamente
ALTER TABLE nyper_storage ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE ownership ENABLE ROW LEVEL SECURITY;
ALTER TABLE cartera ENABLE ROW LEVEL SECURITY;

-- Policies: permitir todo al service_role key (que es la que usa la app)
CREATE POLICY "service_all" ON nyper_storage FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all" ON usuarios FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all" ON ownership FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all" ON cartera FOR ALL USING (true) WITH CHECK (true);
