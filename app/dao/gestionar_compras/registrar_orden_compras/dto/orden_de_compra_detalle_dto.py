class OrdenDeCompraDetalleDto:
    """Detalle de una orden de compra. La tabla orden_compra_det
    guarda id_item (integer), cantidad y precio_unitario."""
    def __init__(self, id_item, cantidad, precio_unitario,
                 item_code=None, item_descripcion=None):
        self.id_item = id_item
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario
        # solo para mostrar / depurar, no se insertan
        self.item_code = item_code
        self.item_descripcion = item_descripcion
