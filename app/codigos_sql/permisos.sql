-- ============================================================
-- PERMISOS POR MÓDULO, VENTANA Y ESCENARIO
--   leer     -> entrar a la ventana / consultar
--   insertar -> agregar (POST)
--   editar   -> modificar / cambiar estado (PUT/PATCH)
--   borrar   -> eliminar / anular (DELETE, o rutas de "anular")
-- Los permisos se asignan por grupo (perfil/rol) en la tabla permisos.
-- ============================================================

ALTER TABLE paginas ADD COLUMN IF NOT EXISTS pag_ruta VARCHAR(200);   -- prefijo de la ventana (HTML)
ALTER TABLE paginas ADD COLUMN IF NOT EXISTS pag_api  VARCHAR(200);   -- prefijo de su API (JSON)

CREATE UNIQUE INDEX IF NOT EXISTS uq_paginas_pag_ruta ON paginas (pag_ruta);

-- La función original referenciaba usuarios.usuario_id, que no existe.
CREATE OR REPLACE FUNCTION get_permisos_usuario(p_usuario_id integer, p_pag_id integer)
RETURNS TABLE(leer boolean, insertar boolean, editar boolean, borrar boolean)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT p.leer, p.insertar, p.editar, p.borrar
    FROM permisos p
    JOIN usuarios u ON u.gru_id = p.gru_id
    WHERE u.usu_id = p_usuario_id AND p.pag_id = p_pag_id;
END;
$$;

-- Todo cambio de permisos queda auditado
DROP TRIGGER IF EXISTS trg_auditoria ON permisos;
CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON permisos
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria();
