-- ============================================================
-- PERMISOS INDIVIDUALES POR USUARIO (excepciones sobre el perfil)
--   La tabla "permisos" define el acceso por PERFIL (gru_id): afecta a
--   todos los usuarios que tengan ese perfil.
--   Esta tabla define excepciones para UN usuario puntual (usu_id), sin
--   tocar el perfil ni afectar a nadie más:
--     NULL  -> no hay excepción: se usa lo que tenga el perfil
--     TRUE  -> a este usuario se le concede aunque el perfil no lo tenga
--     FALSE -> a este usuario se le quita aunque el perfil sí lo tenga
-- ============================================================

CREATE TABLE IF NOT EXISTS permisos_usuario (
    usu_id   INTEGER NOT NULL REFERENCES usuarios(usu_id) ON UPDATE CASCADE ON DELETE CASCADE,
    pag_id   INTEGER NOT NULL REFERENCES paginas(pag_id)  ON UPDATE CASCADE ON DELETE CASCADE,
    leer     BOOLEAN,
    insertar BOOLEAN,
    editar   BOOLEAN,
    borrar   BOOLEAN,
    PRIMARY KEY (usu_id, pag_id)
);

-- Todo cambio de permisos individuales queda auditado (misma función genérica
-- que usan "permisos", "auditoria", etc.)
DROP TRIGGER IF EXISTS trg_auditoria ON permisos_usuario;
CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON permisos_usuario
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
