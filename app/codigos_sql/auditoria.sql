-- ============================================================
-- SISTEMA DE AUDITORÍA
-- Registro completo de transacciones (INSERT/UPDATE/DELETE) sobre
-- las tablas transaccionales del sistema: quién, qué, cuándo.
-- ============================================================

-- ---- Tabla central de auditoría ----
CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria     BIGSERIAL PRIMARY KEY,
    tabla            VARCHAR(100) NOT NULL,
    operacion        VARCHAR(10)  NOT NULL,          -- INSERT / UPDATE / DELETE
    datos_anteriores JSONB,
    datos_nuevos     JSONB,
    usuario          VARCHAR(100) NOT NULL DEFAULT 'sistema',
    fecha_hora       TIMESTAMP    NOT NULL DEFAULT now(),
    resultado        VARCHAR(20)  NOT NULL DEFAULT 'EXITOSO'
);

CREATE INDEX IF NOT EXISTS idx_auditoria_tabla      ON auditoria (tabla);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario     ON auditoria (usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha_hora  ON auditoria (fecha_hora);
CREATE INDEX IF NOT EXISTS idx_auditoria_operacion   ON auditoria (operacion);

-- ---- Función genérica de auditoría (una sola, reutilizada por trigger en cada tabla) ----
-- El usuario responsable se lee de la variable de sesión "myapp.usuario_actual",
-- que la aplicación fija por conexión (ver app/conexion/Conexion.py). Si no está
-- seteada (script suelto, conexión fuera de un request), se registra 'sistema'.
CREATE OR REPLACE FUNCTION fn_auditoria() RETURNS TRIGGER AS $$
DECLARE
    v_usuario TEXT;
BEGIN
    v_usuario := COALESCE(current_setting('myapp.usuario_actual', true), 'sistema');
    IF v_usuario = '' THEN v_usuario := 'sistema'; END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO auditoria(tabla, operacion, datos_anteriores, datos_nuevos, usuario)
        VALUES (TG_TABLE_NAME, TG_OP, NULL, row_to_json(NEW), v_usuario);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auditoria(tabla, operacion, datos_anteriores, datos_nuevos, usuario)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), v_usuario);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO auditoria(tabla, operacion, datos_anteriores, datos_nuevos, usuario)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), NULL, v_usuario);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ---- Variante para "usuarios": redacta el hash de contraseña antes de guardarlo ----
CREATE OR REPLACE FUNCTION fn_auditoria_usuarios() RETURNS TRIGGER AS $$
DECLARE
    v_usuario TEXT;
    v_old JSONB;
    v_new JSONB;
BEGIN
    v_usuario := COALESCE(current_setting('myapp.usuario_actual', true), 'sistema');
    IF v_usuario = '' THEN v_usuario := 'sistema'; END IF;

    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        v_old := row_to_json(OLD)::jsonb - 'usu_clave';
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        v_new := row_to_json(NEW)::jsonb - 'usu_clave';
    END IF;

    INSERT INTO auditoria(tabla, operacion, datos_anteriores, datos_nuevos, usuario)
    VALUES (TG_TABLE_NAME, TG_OP, v_old, v_new, v_usuario);

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---- Protección: los registros de auditoría son inmutables (no UPDATE/DELETE) ----
CREATE OR REPLACE FUNCTION fn_bloquear_alteracion_auditoria() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Los registros de auditoría son inmutables: no se permite % sobre la tabla auditoria', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auditoria_inmutable ON auditoria;
CREATE TRIGGER trg_auditoria_inmutable
    BEFORE UPDATE OR DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_alteracion_auditoria();

-- ---- Asociar el trigger genérico a las tablas transaccionales/cabecera de cada módulo ----
-- (se excluyen tablas puramente de catálogo/referencia: ciudad, país, moneda,
--  unidad_medida, tipo_item, etc. — no aportan trazabilidad de "transacciones importantes")
DO $$
DECLARE
    t TEXT;
    tablas TEXT[] := ARRAY[
        -- Ventas
        'venta_cab', 'venta_det', 'cobro_cab', 'pedido_venta_cab', 'nota_venta_cab',
        -- Compras
        'solicitud_compra_cab', 'presupuesto_compra_cab', 'pedido_compra_cab',
        'orden_compra_cab', 'recepcion_cab', 'factura_compra_cab',
        'compra_cab', 'nota_compra_cab',
        -- Inventario
        'item', 'stock', 'ajuste_cab', 'merma_cab',
        -- Producción
        'orden_prod_cab', 'pedido_produccion_cab', 'presupuesto_prod_cab',
        -- Maestros críticos
        'proveedor', 'cliente'
    ];
BEGIN
    FOREACH t IN ARRAY tablas LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_auditoria ON %I', t);
        EXECUTE format(
            'CREATE TRIGGER trg_auditoria AFTER INSERT OR UPDATE OR DELETE ON %I
             FOR EACH ROW EXECUTE FUNCTION fn_auditoria()', t
        );
    END LOOP;
END $$;

-- ---- usuarios: trigger con la variante que redacta la contraseña ----
DROP TRIGGER IF EXISTS trg_auditoria ON usuarios;
CREATE TRIGGER trg_auditoria
    AFTER INSERT OR UPDATE OR DELETE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_usuarios();
