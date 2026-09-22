-- ============================================================
-- VISTAS DEL SISTEMA
--
-- Convención de nombres:  v_<dominio>_<objeto>
--     seg = seguridad   inv = inventario   ven = ventas   com = compras
-- Cada vista se documenta también en la base con COMMENT ON VIEW
-- (consultable con:  \dv+   o   SELECT obj_description('v_xxx'::regclass)).
--
-- Se pueden recrear en cualquier momento (CREATE OR REPLACE): no guardan datos,
-- solo la consulta. Si cambia una tabla base, se ajusta aquí y todo el sistema
-- que consulta la vista se actualiza sin tocar el código Python.
-- ============================================================


-- ------------------------------------------------------------
-- ÍNDICES que sostienen a las vistas (evitan recorrer tablas completas:
-- stock tiene ~344.000 filas e item ~86.000)
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_venta_det_item_code        ON venta_det (item_code);
CREATE INDEX IF NOT EXISTS idx_venta_det_cab              ON venta_det (id_venta_cab);
CREATE INDEX IF NOT EXISTS idx_stock_sucursal_deposito    ON stock (id_sucursal, id_deposito);
CREATE INDEX IF NOT EXISTS idx_recepcion_det_item_code    ON recepcion_det (item_code);
CREATE INDEX IF NOT EXISTS idx_recepcion_det_recepcion    ON recepcion_det (id_recepcion);
CREATE INDEX IF NOT EXISTS idx_solicitud_det_solicitud    ON solicitud_compra_det (id_solicitud);
CREATE INDEX IF NOT EXISTS idx_pedido_det_cab             ON pedido_compra_det (id_pedido_compra_cab);
CREATE INDEX IF NOT EXISTS idx_factura_recepcion          ON factura_compra_cab (id_recepcion);


-- ============================================================
-- SEGURIDAD
-- ============================================================

-- Usuarios SIN exponer la contraseña (vista de seguridad).
-- Cualquier reporte o pantalla debe consultar esta vista y no la tabla usuarios.
CREATE OR REPLACE VIEW v_seg_usuarios AS
SELECT
    u.usu_id                                   AS id_usuario,
    TRIM(u.usu_nick)                           AS usuario,
    u.usu_email                                AS correo,
    g.gru_id                                   AS id_perfil,
    g.gru_des                                  AS perfil,
    u.fun_id                                   AS id_funcionario,
    TRIM(CONCAT(p.nombres, ' ', p.apellidos))  AS persona,
    u.usu_estado                               AS activo,
    u.usu_nro_intentos                         AS intentos_fallidos
    -- usu_clave se excluye a propósito
FROM usuarios u
JOIN grupos g          ON g.gru_id = u.gru_id
LEFT JOIN personas p   ON p.id_persona = u.fun_id;

COMMENT ON VIEW v_seg_usuarios IS
'Seguridad. Usuarios con su perfil y estado de bloqueo, SIN la contraseña. Depende de: usuarios, grupos, personas.';


-- Permisos por perfil, con nombres legibles de módulo y ventana.
CREATE OR REPLACE VIEW v_seg_permisos AS
SELECT
    g.gru_id       AS id_perfil,
    g.gru_des      AS perfil,
    m.mod_des      AS modulo,
    p.pag_id       AS id_ventana,
    p.pag_nombre   AS ventana,
    p.pag_ruta     AS ruta,
    pe.leer        AS puede_ver,
    pe.insertar    AS puede_agregar,
    pe.editar      AS puede_modificar,
    pe.borrar      AS puede_eliminar
FROM permisos pe
JOIN grupos g   ON g.gru_id = pe.gru_id
JOIN paginas p  ON p.pag_id = pe.pag_id
JOIN modulos m  ON m.mod_id = p.mod_id;

COMMENT ON VIEW v_seg_permisos IS
'Seguridad. Matriz de permisos (ver/agregar/modificar/eliminar) por perfil, módulo y ventana. Depende de: permisos, grupos, paginas, modulos.';


-- Intentos fallidos de acceso agrupados por día e IP (base para detectar fuerza bruta).
CREATE OR REPLACE VIEW v_seg_accesos_fallidos AS
SELECT
    fecha_hora::date                    AS fecha,
    ip,
    COUNT(*)                            AS intentos_fallidos,
    COUNT(DISTINCT usuario_intentado)   AS usuarios_distintos,
    MAX(fecha_hora)                     AS ultimo_intento
FROM log_acceso
WHERE evento IN ('LOGIN_FALLIDO', 'USUARIO_INEXISTENTE', '2FA_FALLIDO', 'ACCESO_DENEGADO')
GROUP BY fecha_hora::date, ip;

COMMENT ON VIEW v_seg_accesos_fallidos IS
'Seguridad. Intentos fallidos de ingreso por día e IP. Depende de: log_acceso.';


-- Actividad sospechosa: 3 o más fallos desde una misma IP en un día, o una IP probando 3+ usuarios.
CREATE OR REPLACE VIEW v_seg_accesos_sospechosos AS
SELECT *
FROM v_seg_accesos_fallidos
WHERE intentos_fallidos >= 3
   OR usuarios_distintos >= 3;

COMMENT ON VIEW v_seg_accesos_sospechosos IS
'Seguridad. Subconjunto de v_seg_accesos_fallidos con patrón anómalo (>=3 fallos o >=3 usuarios distintos desde la misma IP en el día).';


-- ============================================================
-- INVENTARIO
-- ============================================================

-- Stock por producto, sucursal y depósito, con el nivel de riesgo respecto al mínimo.
-- Los umbrales son los mismos que usa el dashboard (ver DashboardDao._nivel_riesgo):
--   <= 0 SIN_STOCK | <= 50% del mínimo CRITICO | <= mínimo BAJO | <= 150% del mínimo ATENCION | resto NORMAL
CREATE OR REPLACE VIEW v_inv_stock_detalle AS
SELECT
    s.id_stock,
    i.id_item,
    i.item_code                                AS codigo,
    i.descripcion                              AS producto,
    i.activo                                   AS producto_activo,
    su.id_sucursal,
    su.descripcion                             AS sucursal,
    d.id_deposito,
    d.descripcion                              AS deposito,
    s.cantidad                                 AS stock_actual,
    COALESCE(i.cantidad_minima, 0)             AS stock_minimo,
    CASE
        WHEN s.cantidad <= 0                                       THEN 'SIN_STOCK'
        WHEN COALESCE(i.cantidad_minima, 0) <= 0                   THEN 'NORMAL'
        WHEN s.cantidad <= i.cantidad_minima * 0.5                 THEN 'CRITICO'
        WHEN s.cantidad <= i.cantidad_minima                       THEN 'BAJO'
        WHEN s.cantidad <= i.cantidad_minima * 1.5                 THEN 'ATENCION'
        ELSE 'NORMAL'
    END                                        AS nivel_stock,
    s.fecha_ultima_actualizacion
FROM stock s
JOIN item i       ON i.id_item = s.id_item
JOIN sucursal su  ON su.id_sucursal = s.id_sucursal
JOIN deposito d   ON d.id_deposito = s.id_deposito;

COMMENT ON VIEW v_inv_stock_detalle IS
'Inventario. Una fila por producto/sucursal/depósito con stock, mínimo y nivel (SIN_STOCK, CRITICO, BAJO, ATENCION, NORMAL). Depende de: stock, item, sucursal, deposito. Usa idx_stock_item e idx_stock_sucursal_deposito.';


-- Resumen de ventas por producto (solo ventas PAGADAS): última venta, unidades e importe.
CREATE OR REPLACE VIEW v_inv_item_ventas AS
SELECT
    i.id_item,
    i.item_code                             AS codigo,
    MAX(v.fecha_venta)                      AS ultima_venta,
    SUM(vd.cantidad)                        AS unidades_vendidas,
    SUM(vd.cantidad * vd.precio_unitario)   AS importe_vendido,
    COUNT(DISTINCT v.id_venta_cab)          AS cantidad_ventas
FROM venta_det vd
JOIN venta_cab v  ON v.id_venta_cab = vd.id_venta_cab
JOIN item i       ON i.item_code = vd.item_code
WHERE v.estado = 'PAGADO'
GROUP BY i.id_item, i.item_code;

COMMENT ON VIEW v_inv_item_ventas IS
'Inventario. Por producto vendido: fecha de la última venta, unidades e importe acumulados (historial completo, solo PAGADO). Depende de: venta_det, venta_cab, item. Usa idx_venta_det_item_code.';


-- ============================================================
-- VENTAS
-- ============================================================

-- Una fila por línea de venta, con cliente, sucursal y producto ya resueltos.
CREATE OR REPLACE VIEW v_ven_venta_detalle AS
SELECT
    v.id_venta_cab,
    v.codigo_venta,
    v.fecha_venta,
    v.estado,
    su.descripcion                        AS sucursal,
    c.clie_nombre                         AS cliente,
    vd.id_venta_det,
    vd.item_code                          AS codigo,
    i.descripcion                         AS producto,
    vd.cantidad,
    vd.precio_unitario,
    vd.cantidad * vd.precio_unitario      AS subtotal,
    v.total_venta
FROM venta_cab v
JOIN venta_det vd       ON vd.id_venta_cab = v.id_venta_cab
LEFT JOIN item i        ON i.item_code = vd.item_code
LEFT JOIN sucursal su   ON su.id_sucursal = v.id_sucursal
LEFT JOIN cliente c     ON c.id_clie = v.id_cliente;

COMMENT ON VIEW v_ven_venta_detalle IS
'Ventas. Detalle de cada venta con cliente, sucursal, producto y subtotal por línea. Depende de: venta_cab, venta_det, item, sucursal, cliente.';


-- Totales de venta por día y sucursal (solo PAGADAS).
CREATE OR REPLACE VIEW v_ven_ventas_diarias AS
SELECT
    v.fecha_venta                          AS fecha,
    v.id_sucursal,
    su.descripcion                         AS sucursal,
    COUNT(*)                               AS cantidad_ventas,
    SUM(v.total_venta)                     AS total_vendido,
    COALESCE(SUM(u.unidades), 0)           AS unidades_vendidas
FROM venta_cab v
LEFT JOIN sucursal su ON su.id_sucursal = v.id_sucursal
-- las unidades se suman aparte para no duplicar total_venta al unir con el detalle
LEFT JOIN (
    SELECT id_venta_cab, SUM(cantidad) AS unidades
    FROM venta_det
    GROUP BY id_venta_cab
) u ON u.id_venta_cab = v.id_venta_cab
WHERE v.estado = 'PAGADO'
GROUP BY v.fecha_venta, v.id_sucursal, su.descripcion;

COMMENT ON VIEW v_ven_ventas_diarias IS
'Ventas. Cantidad de ventas, importe total y unidades por día y sucursal (solo PAGADO). Depende de: venta_cab, venta_det, sucursal. Usa idx_venta_fecha e idx_venta_det_cab.';


-- ============================================================
-- COMPRAS
-- ============================================================

-- Solicitudes de compra con solicitante, sucursal y depósito (listado de la ventana).
CREATE OR REPLACE VIEW v_com_solicitud AS
SELECT
    sc.id_solicitud,
    sc.nro_solicitud,
    sc.fecha_solicitud,
    f.nombres || ' ' || f.apellidos   AS solicitante,
    s.descripcion                     AS sucursal,
    d.descripcion                     AS deposito,
    sc.estado,
    (SELECT COUNT(*) FROM solicitud_compra_det sd
      WHERE sd.id_solicitud = sc.id_solicitud) AS cantidad_items,
    (SELECT MIN(sd.fecha_necesaria) FROM solicitud_compra_det sd
      WHERE sd.id_solicitud = sc.id_solicitud) AS fecha_necesaria
FROM solicitud_compra_cab sc
LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
LEFT JOIN sucursal s     ON s.id_sucursal = sc.id_sucursal
LEFT JOIN deposito d     ON d.id_deposito = sc.id_deposito AND d.activo = TRUE;

COMMENT ON VIEW v_com_solicitud IS
'Compras. Solicitudes de compra con solicitante, sucursal, depósito, estado, cantidad de ítems y fecha necesaria. Depende de: solicitud_compra_cab/det, funcionarios, sucursal, deposito.';


-- Presupuestos con proveedor y funcionario.
CREATE OR REPLACE VIEW v_com_presupuesto AS
SELECT
    pc.id_pre_compra_cab      AS id_presupuesto,
    pc.cod_presupuesto,
    pc.fecha_emision,
    pc.fecha_vencimiento,
    p.prov_nombre             AS proveedor,
    f.nombres || ' ' || f.apellidos AS funcionario,
    pc.id_solicitud,
    pc.estado
FROM presupuesto_compra_cab pc
LEFT JOIN proveedor p    ON p.id_proveedor = pc.id_proveedor
LEFT JOIN funcionarios f ON f.fun_id = pc.fun_id;

COMMENT ON VIEW v_com_presupuesto IS
'Compras. Presupuestos con proveedor, funcionario, solicitud de origen y estado. Depende de: presupuesto_compra_cab, proveedor, funcionarios.';


-- Pedidos de compra con proveedor, sucursal, depósito y total calculado del detalle.
CREATE OR REPLACE VIEW v_com_pedido AS
SELECT
    pd.id_pedido_compra_cab   AS id_pedido,
    pd.nro_pedido,
    pd.fecha_pedido,
    p.prov_nombre             AS proveedor,
    s.descripcion             AS sucursal,
    d.descripcion             AS deposito,
    pd.id_solicitud,
    pd.id_pre_compra_cab      AS id_presupuesto,
    pd.estado,
    COALESCE(t.cantidad_items, 0) AS cantidad_items,
    COALESCE(t.total_pedido, 0)   AS total_pedido
FROM pedido_compra_cab pd
LEFT JOIN proveedor p  ON p.id_proveedor = pd.id_proveedor
LEFT JOIN sucursal s   ON s.id_sucursal = pd.id_sucursal
LEFT JOIN deposito d   ON d.id_deposito = pd.id_deposito
LEFT JOIN (
    SELECT id_pedido_compra_cab,
           COUNT(*)                          AS cantidad_items,
           SUM(cant_pedido * costo_unitario) AS total_pedido
    FROM pedido_compra_det
    GROUP BY id_pedido_compra_cab
) t ON t.id_pedido_compra_cab = pd.id_pedido_compra_cab;

COMMENT ON VIEW v_com_pedido IS
'Compras. Pedidos con proveedor, sucursal, depósito, cantidad de ítems y total (cantidad x costo). Depende de: pedido_compra_cab/det, proveedor, sucursal, deposito. Usa idx_pedido_det_cab.';


-- Facturas de compra con proveedor y número de recepción.
CREATE OR REPLACE VIEW v_com_factura AS
SELECT
    f.id_factura,
    f.nro_factura,
    f.fecha_emision,
    f.fecha_vencimiento,
    p.prov_nombre    AS proveedor,
    r.nro_recepcion,
    f.monto_total,
    f.estado,
    f.fecha_pago
FROM factura_compra_cab f
LEFT JOIN proveedor p     ON p.id_proveedor = f.id_proveedor
LEFT JOIN recepcion_cab r ON r.id_recepcion = f.id_recepcion;

COMMENT ON VIEW v_com_factura IS
'Compras. Facturas de proveedor con proveedor, recepción asociada, monto y estado. Depende de: factura_compra_cab, proveedor, recepcion_cab.';


-- Libro de compras con la factura y el tipo de impuesto resueltos.
CREATE OR REPLACE VIEW v_com_libro_compras AS
SELECT
    l.id_libro_compras,
    l.fecha_emision,
    f.nro_factura,
    p.prov_nombre        AS proveedor,
    ti.descripcion       AS tipo_impuesto,
    l.monto
FROM libro_compras l
LEFT JOIN factura_compra_cab f ON f.id_factura = l.id_factura
LEFT JOIN proveedor p          ON p.id_proveedor = f.id_proveedor
LEFT JOIN tipo_impuesto ti     ON ti.id_tipo_impuesto = l.tipo_impuesto;

COMMENT ON VIEW v_com_libro_compras IS
'Compras. Asientos del libro de compras con factura, proveedor y tipo de impuesto. Depende de: libro_compras, factura_compra_cab, proveedor, tipo_impuesto.';


-- ============================================================
-- ACCESO POR ROL
-- Un rol de solo lectura para reportes: ve las vistas, no las tablas base
-- (en particular no ve usuarios.usu_clave).
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_reportes') THEN
        CREATE ROLE rol_reportes NOLOGIN;
    END IF;
END $$;

GRANT SELECT ON
    v_seg_usuarios, v_seg_permisos, v_seg_accesos_fallidos, v_seg_accesos_sospechosos,
    v_inv_stock_detalle, v_inv_item_ventas,
    v_ven_venta_detalle, v_ven_ventas_diarias,
    v_com_solicitud, v_com_presupuesto, v_com_pedido, v_com_factura, v_com_libro_compras
TO rol_reportes;
