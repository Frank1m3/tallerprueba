-- ============================================================
-- PRESUPUESTO: sucursal y depósito de destino
--
-- Un presupuesto que nace de una solicitud hereda su sucursal y depósito (así el pedido
-- "Desde Presupuesto" los carga solo). Un presupuesto cargado a mano sin solicitud guarda
-- la sucursal elegida en el formulario.
-- ============================================================

ALTER TABLE presupuesto_compra_cab ADD COLUMN IF NOT EXISTS id_sucursal INTEGER REFERENCES sucursal(id_sucursal);
ALTER TABLE presupuesto_compra_cab ADD COLUMN IF NOT EXISTS id_deposito INTEGER REFERENCES deposito(id_deposito);

-- Al insertar con solicitud de origen, la solicitud manda: es de donde sale la necesidad.
CREATE OR REPLACE FUNCTION fn_presupuesto_destino() RETURNS TRIGGER AS $$
DECLARE
    v_suc INTEGER;
    v_dep INTEGER;
BEGIN
    IF NEW.id_solicitud IS NOT NULL THEN
        SELECT id_sucursal, id_deposito INTO v_suc, v_dep
        FROM solicitud_compra_cab WHERE id_solicitud = NEW.id_solicitud;
        NEW.id_sucursal := COALESCE(v_suc, NEW.id_sucursal);
        NEW.id_deposito := COALESCE(v_dep, NEW.id_deposito);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_presupuesto_destino ON presupuesto_compra_cab;
CREATE TRIGGER trg_presupuesto_destino BEFORE INSERT ON presupuesto_compra_cab
    FOR EACH ROW EXECUTE FUNCTION fn_presupuesto_destino();

-- Presupuestos ya existentes con solicitud de origen
UPDATE presupuesto_compra_cab pc
SET id_sucursal = sc.id_sucursal, id_deposito = sc.id_deposito
FROM solicitud_compra_cab sc
WHERE sc.id_solicitud = pc.id_solicitud AND pc.id_sucursal IS NULL;
