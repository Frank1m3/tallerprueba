-- ============================================================
-- PORTAL DEL PROVEEDOR: invitaciones para cotizar una solicitud
--
-- Cada invitación es un enlace único (/cotizar/<token>) que se le envía a un proveedor.
-- El token NO se guarda: solo su hash SHA-256, así que ni la base ni los respaldos
-- permiten reconstruir un enlace válido. Al responder, el proveedor genera su presupuesto
-- (presupuesto_compra_cab/det) para la solicitud.
-- ============================================================

CREATE TABLE IF NOT EXISTS cotizacion_invitacion (
    id_invitacion      SERIAL PRIMARY KEY,
    id_solicitud       INTEGER NOT NULL REFERENCES solicitud_compra_cab(id_solicitud),
    id_proveedor       INTEGER NOT NULL REFERENCES proveedor(id_proveedor),
    token_hash         CHAR(64) NOT NULL UNIQUE,
    email_destino      VARCHAR(150),
    mensaje            TEXT,
    fecha_limite       DATE NOT NULL,
    estado             VARCHAR(15) NOT NULL DEFAULT 'PENDIENTE'
                       CHECK (estado IN ('PENDIENTE', 'RESPONDIDA', 'CANCELADA')),
    id_pre_compra_cab  INTEGER REFERENCES presupuesto_compra_cab(id_pre_compra_cab),
    observaciones      TEXT,
    enviada_por        VARCHAR(100),
    fun_id             INTEGER,
    fecha_envio        TIMESTAMP NOT NULL DEFAULT now(),
    fecha_respuesta    TIMESTAMP,
    ip_respuesta       VARCHAR(64)
);

-- Una sola invitación vigente por proveedor y solicitud (las canceladas no cuentan)
CREATE UNIQUE INDEX IF NOT EXISTS uq_invitacion_vigente
    ON cotizacion_invitacion (id_solicitud, id_proveedor) WHERE estado <> 'CANCELADA';
CREATE INDEX IF NOT EXISTS idx_invitacion_solicitud ON cotizacion_invitacion (id_solicitud);

COMMENT ON TABLE cotizacion_invitacion IS
'Compras. Invitaciones a proveedores para cotizar una solicitud aprobada (portal /cotizar/<token>). Guarda solo el hash del token.';

-- Auditoría de cambios (sin el hash del token)
CREATE OR REPLACE FUNCTION fn_auditoria_invitacion() RETURNS TRIGGER AS $$
DECLARE
    v_usuario TEXT;
    v_old JSONB;
    v_new JSONB;
BEGIN
    v_usuario := COALESCE(NULLIF(current_setting('myapp.usuario_actual', true), ''), 'sistema');
    IF TG_OP IN ('UPDATE', 'DELETE') THEN v_old := row_to_json(OLD)::jsonb - 'token_hash'; END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN v_new := row_to_json(NEW)::jsonb - 'token_hash'; END IF;
    INSERT INTO auditoria(tabla, operacion, datos_anteriores, datos_nuevos, usuario)
    VALUES (TG_TABLE_NAME, TG_OP, v_old, v_new, v_usuario);
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auditoria ON cotizacion_invitacion;
CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON cotizacion_invitacion
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_invitacion();
