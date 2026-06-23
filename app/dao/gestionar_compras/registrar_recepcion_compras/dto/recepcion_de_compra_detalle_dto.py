from typing import Optional


class RecepcionDetalleDto:
<<<<<<< Updated upstream
    """
    DTO para el detalle de una recepción de mercadería.
    Representa cada ítem recibido junto con cantidad pedida y cantidad recibida.
    """

    def __init__(
        self,
        id_pedido_det: int,             # NUEVO: id del detalle del pedido
=======
    """Detalle de recepción vinculado a orden de compra e ítem."""

    def __init__(
        self,
        id_orden_compra_det: Optional[int] = None,
        id_item: Optional[int] = None,
        id_pedido_det: Optional[int] = None,
>>>>>>> Stashed changes
        item_code: str = '',
        descripcion: str = '',
        cantidad_pedida: float = 0.0,
        cantidad_recibida: float = 0.0,
        costo_unitario: float = 0.0,
        fecha_vencimiento: Optional[str] = None,
        unidad_med: Optional[int] = None
    ):
        self.__id_orden_compra_det = id_orden_compra_det
        self.__id_item = id_item
        self.__id_pedido_det = id_pedido_det
        self.__item_code = item_code
        self.__descripcion = descripcion
        self.__cantidad_pedida = float(cantidad_pedida)
        self.__cantidad_recibida = float(cantidad_recibida)
        self.__costo_unitario = float(costo_unitario)
        self.__fecha_vencimiento = fecha_vencimiento
        self.__unidad_med = unidad_med

    @property
    def id_orden_compra_det(self) -> Optional[int]:
        return self.__id_orden_compra_det

    @property
    def id_item(self) -> Optional[int]:
        return self.__id_item

    @property
    def id_pedido_det(self) -> int:
        return self.__id_pedido_det
<<<<<<< Updated upstream
    @id_pedido_det.setter
    def id_pedido_det(self, valor: int):
        if valor <= 0:
            raise ValueError("id_pedido_det debe ser > 0")
        self.__id_pedido_det = valor
=======
>>>>>>> Stashed changes

    @property
    def item_code(self) -> str:
        return self.__item_code

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    @property
    def cantidad_pedida(self) -> float:
        return self.__cantidad_pedida

    @property
    def cantidad_recibida(self) -> float:
        return self.__cantidad_recibida

    @property
    def costo_unitario(self) -> float:
        return self.__costo_unitario

    def to_dict(self):
        return {
            'id_orden_compra_det': self.id_orden_compra_det,
            'id_item': self.id_item,
            'item_code': self.item_code,
            'descripcion': self.descripcion,
            'cantidad_pedida': self.cantidad_pedida,
            'cantidad_recibida': self.cantidad_recibida,
            'costo_unitario': self.costo_unitario
        }
