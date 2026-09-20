-- ============================================================
-- LOG DE INTENTOS DE ACCESO
-- Registra cada intento de ingreso (usuario, resultado, fecha y hora, IP).
-- Nunca se guarda la contraseña ingresada: solo el resultado del intento.
-- ============================================================

CREATE TABLE IF NOT EXISTS log_acceso (
    id_log             BIGSERIAL PRIMARY KEY,
    usuario_intentado  VARCHAR(100) NOT NULL,
    id_usuario         INTEGER,
    evento             VARCHAR(40)  NOT NULL,
    detalle            TEXT,
    ip                 VARCHAR(64),
    user_agent         TEXT,
    fecha_hora         TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_log_acceso_fecha   ON log_acceso (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_log_acceso_usuario ON log_acceso (usuario_intentado);
CREATE INDEX IF NOT EXISTS idx_log_acceso_evento  ON log_acceso (evento);
CREATE INDEX IF NOT EXISTS idx_log_acceso_ip      ON log_acceso (ip);

-- Mensaje genérico para cualquier tabla de registro inmutable
CREATE OR REPLACE FUNCTION fn_bloquear_alteracion_auditoria() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Los registros de % son inmutables: no se permite %', TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_acceso_inmutable ON log_acceso;
CREATE TRIGGER trg_log_acceso_inmutable
    BEFORE UPDATE OR DELETE ON log_acceso
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_alteracion_auditoria();
