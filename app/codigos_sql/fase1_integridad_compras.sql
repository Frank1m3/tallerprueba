-- =============================================================================
-- FASE 1: Integridad de datos, flujo Compras e Inventario
-- Base: TALLER (PostgreSQL)
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Crear ítems faltantes a partir de detalles históricos
-- ---------------------------------------------------------------------------
INSERT INTO item (item_code, descripcion, activo, precio_unitario)
SELECT DISTINCT
    CASE
        WHEN TRIM(COALESCE(p.item_code, '')) = '' THEN 'GEN-PED-' || p.id_pedido_compra_det::text
        ELSE TRIM(p.item_code)
    END,
    TRIM(p.item_descripcion),
    TRUE,
    COALESCE(p.costo_unitario, 0)
FROM pedido_compra_det p
WHERE TRIM(COALESCE(p.item_descripcion, '')) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM item i
      WHERE UPPER(TRIM(i.item_code)) = UPPER(
          CASE
              WHEN TRIM(COALESCE(p.item_code, '')) = '' THEN 'GEN-PED-' || p.id_pedido_compra_det::text
              ELSE TRIM(p.item_code)
          END
      )
  );

INSERT INTO item (item_code, descripcion, activo, precio_unitario)
SELECT DISTINCT
    TRIM(pd.item_code),
    COALESCE(i.descripcion, TRIM(pd.item_code)),
    TRUE,
    COALESCE(pd.precio_unitario, 0)
FROM presupuesto_compra_det pd
LEFT JOIN item i ON UPPER(TRIM(i.item_code)) = UPPER(TRIM(pd.item_code))
WHERE TRIM(COALESCE(pd.item_code, '')) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM item ix WHERE UPPER(TRIM(ix.item_code)) = UPPER(TRIM(pd.item_code))
  );

-- ---------------------------------------------------------------------------
-- 2. Normalizar id_item en tablas de detalle
-- ---------------------------------------------------------------------------
ALTER TABLE pedido_compra_det ADD COLUMN IF NOT EXISTS id_item INTEGER;
UPDATE pedido_compra_det p
SET id_item = i.id_item
FROM item i
WHERE p.id_item IS NULL
  AND UPPER(TRIM(i.item_code)) = UPPER(
      CASE
          WHEN TRIM(COALESCE(p.item_code, '')) = '' THEN 'GEN-PED-' || p.id_pedido_compra_det::text
          ELSE TRIM(p.item_code)
      END
  );

ALTER TABLE presupuesto_compra_det ADD COLUMN IF NOT EXISTS id_item INTEGER;
UPDATE presupuesto_compra_det pd
SET id_item = i.id_item
FROM item i
WHERE pd.id_item IS NULL
  AND UPPER(TRIM(i.item_code)) = UPPER(TRIM(pd.item_code));

ALTER TABLE venta_det ADD COLUMN IF NOT EXISTS id_item INTEGER;
UPDATE venta_det vd
SET id_item = i.id_item
FROM item i
WHERE vd.id_item IS NULL
  AND vd.item_code IS NOT NULL
  AND UPPER(TRIM(i.item_code)) = UPPER(TRIM(vd.item_code));

ALTER TABLE recepcion_det ADD COLUMN IF NOT EXISTS id_item INTEGER;
UPDATE recepcion_det rd
SET id_item = i.id_item
FROM item i
WHERE rd.id_item IS NULL
  AND UPPER(TRIM(i.item_code)) = UPPER(TRIM(rd.item_code));

-- ---------------------------------------------------------------------------
-- 3. Orden de compra: número correlativo y depósito destino
-- ---------------------------------------------------------------------------
ALTER TABLE orden_compra_cab ADD COLUMN IF NOT EXISTS nro_orden VARCHAR(20);
ALTER TABLE orden_compra_cab ADD COLUMN IF NOT EXISTS id_deposito INTEGER;

UPDATE orden_compra_cab
SET nro_orden = 'OC-' || id_orden_compra_cab::text
WHERE nro_orden IS NULL;

CREATE SEQUENCE IF NOT EXISTS seq_nro_orden_compra START 1;

-- ---------------------------------------------------------------------------
-- 4. Recepción vinculada a Orden de Compra
-- ---------------------------------------------------------------------------
ALTER TABLE recepcion_cab ADD COLUMN IF NOT EXISTS id_orden_compra_cab INTEGER;
ALTER TABLE recepcion_cab ALTER COLUMN id_pedido DROP NOT NULL;

ALTER TABLE recepcion_det ADD COLUMN IF NOT EXISTS id_orden_compra_det INTEGER;

-- Migrar recepciones históricas (referencia legacy al pedido)
UPDATE recepcion_cab rc
SET id_orden_compra_cab = oc.id_orden_compra_cab
FROM orden_compra_cab oc
WHERE rc.id_orden_compra_cab IS NULL
  AND oc.id_pre_compra_cab IS NOT NULL
  AND EXISTS (
      SELECT 1 FROM pedido_compra_cab pc
      WHERE pc.id_pedido_compra_cab = rc.id_pedido
  );

-- ---------------------------------------------------------------------------
-- 5. Consolidar stock duplicado y agregar UNIQUE
-- ---------------------------------------------------------------------------
UPDATE stock s
SET cantidad = agg.total
FROM (
    SELECT id_sucursal, id_deposito, id_item,
           SUM(cantidad) AS total,
           MIN(id_stock) AS keep_id
    FROM stock
    GROUP BY id_sucursal, id_deposito, id_item
) agg
WHERE s.id_stock = agg.keep_id;

DELETE FROM stock s
USING stock s2
WHERE s.id_stock > s2.id_stock
  AND s.id_sucursal IS NOT DISTINCT FROM s2.id_sucursal
  AND s.id_deposito IS NOT DISTINCT FROM s2.id_deposito
  AND s.id_item = s2.id_item;

CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_sucursal_deposito_item
    ON stock (id_sucursal, id_deposito, id_item);

-- ---------------------------------------------------------------------------
-- 6. Corregir aperturas: FK hacia funcionarios (la app usa fun_id)
-- ---------------------------------------------------------------------------
ALTER TABLE aperturas DROP CONSTRAINT IF EXISTS aperturas_cajero_fkey;
ALTER TABLE aperturas DROP CONSTRAINT IF EXISTS aperturas_clave_fiscal_fkey;

ALTER TABLE aperturas
    ADD CONSTRAINT aperturas_cajero_fkey
        FOREIGN KEY (cajero) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE aperturas
    ADD CONSTRAINT aperturas_clave_fiscal_fkey
        FOREIGN KEY (clave_fiscal) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

-- ---------------------------------------------------------------------------
-- 7. Claves foráneas faltantes en compras
-- ---------------------------------------------------------------------------
ALTER TABLE pedido_compra_cab DROP CONSTRAINT IF EXISTS pedido_compra_cab_id_funcionario_fkey;
ALTER TABLE pedido_compra_cab
    ADD CONSTRAINT pedido_compra_cab_id_funcionario_fkey
        FOREIGN KEY (id_funcionario) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE pedido_compra_det DROP CONSTRAINT IF EXISTS pedido_compra_det_id_item_fkey;
ALTER TABLE pedido_compra_det
    ADD CONSTRAINT pedido_compra_det_id_item_fkey
        FOREIGN KEY (id_item) REFERENCES item(id_item)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE presupuesto_compra_det DROP CONSTRAINT IF EXISTS presupuesto_compra_det_id_item_fkey;
ALTER TABLE presupuesto_compra_det
    ADD CONSTRAINT presupuesto_compra_det_id_item_fkey
        FOREIGN KEY (id_item) REFERENCES item(id_item)
        ON DELETE RESTRICT ON UPDATE CASCADE;

UPDATE presupuesto_compra_cab
SET fun_id = NULL
WHERE fun_id IS NOT NULL
  AND fun_id NOT IN (SELECT fun_id FROM funcionarios);

UPDATE pedido_compra_cab
SET id_funcionario = NULL
WHERE id_funcionario IS NOT NULL
  AND id_funcionario NOT IN (SELECT fun_id FROM funcionarios);

UPDATE orden_compra_cab
SET fun_id = NULL
WHERE fun_id IS NOT NULL
  AND fun_id NOT IN (SELECT fun_id FROM funcionarios);

ALTER TABLE presupuesto_compra_cab DROP CONSTRAINT IF EXISTS presupuesto_compra_cab_fun_id_fkey;
ALTER TABLE presupuesto_compra_cab
    ADD CONSTRAINT presupuesto_compra_cab_fun_id_fkey
        FOREIGN KEY (fun_id) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE orden_compra_cab DROP CONSTRAINT IF EXISTS orden_compra_cab_id_pre_compra_cab_fkey;
ALTER TABLE orden_compra_cab
    ADD CONSTRAINT orden_compra_cab_id_pre_compra_cab_fkey
        FOREIGN KEY (id_pre_compra_cab) REFERENCES presupuesto_compra_cab(id_pre_compra_cab)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE orden_compra_cab DROP CONSTRAINT IF EXISTS orden_compra_cab_fun_id_fkey;
ALTER TABLE orden_compra_cab
    ADD CONSTRAINT orden_compra_cab_fun_id_fkey
        FOREIGN KEY (fun_id) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE orden_compra_cab DROP CONSTRAINT IF EXISTS orden_compra_cab_id_deposito_fkey;
ALTER TABLE orden_compra_cab
    ADD CONSTRAINT orden_compra_cab_id_deposito_fkey
        FOREIGN KEY (id_deposito) REFERENCES deposito(id_deposito)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE recepcion_cab DROP CONSTRAINT IF EXISTS recepcion_cab_id_orden_compra_cab_fkey;
ALTER TABLE recepcion_cab
    ADD CONSTRAINT recepcion_cab_id_orden_compra_cab_fkey
        FOREIGN KEY (id_orden_compra_cab) REFERENCES orden_compra_cab(id_orden_compra_cab)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE recepcion_det DROP CONSTRAINT IF EXISTS recepcion_det_id_orden_compra_det_fkey;
ALTER TABLE recepcion_det
    ADD CONSTRAINT recepcion_det_id_orden_compra_det_fkey
        FOREIGN KEY (id_orden_compra_det) REFERENCES orden_compra_det(id_orden_compra_det)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE recepcion_det DROP CONSTRAINT IF EXISTS recepcion_det_id_item_fkey;
ALTER TABLE recepcion_det
    ADD CONSTRAINT recepcion_det_id_item_fkey
        FOREIGN KEY (id_item) REFERENCES item(id_item)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE venta_det DROP CONSTRAINT IF EXISTS venta_det_id_item_fkey;
ALTER TABLE venta_det
    ADD CONSTRAINT venta_det_id_item_fkey
        FOREIGN KEY (id_item) REFERENCES item(id_item)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE venta_cab DROP CONSTRAINT IF EXISTS venta_cab_fun_id_fkey;
ALTER TABLE venta_cab
    ADD CONSTRAINT venta_cab_fun_id_fkey
        FOREIGN KEY (fun_id) REFERENCES funcionarios(fun_id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE cobro_det DROP CONSTRAINT IF EXISTS cobro_det_id_forma_cobro_fkey;
ALTER TABLE cobro_det
    ADD CONSTRAINT cobro_det_id_forma_cobro_fkey
        FOREIGN KEY (id_forma_cobro) REFERENCES formas_pago(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

-- ---------------------------------------------------------------------------
-- 8. Enum solicitud: unificar ANULADO
-- ---------------------------------------------------------------------------
UPDATE solicitud_compra_cab SET estado = 'ANULADO' WHERE estado = 'ANULADA';

COMMIT;
