class OrdenDeComprasDto:
    """Cabecera de una orden de compra (orden_compra_cab)."""
    def __init__(self, id_sucursal, fun_id, fecha_emision, id_proveedor,
                 detalle_orden, id_pre_compra_cab=None, estado='PENDIENTE'):
        self.id_pre_compra_cab = id_pre_compra_cab
        self.id_sucursal = id_sucursal
        self.fun_id = fun_id
        self.fecha_emision = fecha_emision
        self.id_proveedor = id_proveedor
        self.estado = estado
        self.detalle_orden = detalle_orden
