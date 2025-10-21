from typing import Optional

class RecepcionDetalleDto:
    """
    DTO para el detalle de una recepción de mercadería.
    Representa cada ítem recibido junto con cantidad pedida y cantidad recibida.
    """

    def __init__(
        self,
        item_code: str = '',
        descripcion: str = '',
        cantidad_pedida: float = 0.0,
        cantidad_recibida: float = 0.0,
        fecha_vencimiento: Optional[str] = None,
        unidad_med: Optional[int] = None
    ):
        self.__item_code = item_code
        self.__descripcion = descripcion
        self.__cantidad_pedida = float(cantidad_pedida)
        self.__cantidad_recibida = float(cantidad_recibida)
        self.__fecha_vencimiento = fecha_vencimiento
        self.__unidad_med = unidad_med

    # ---------------------------
    # Propiedades
    # ---------------------------
    @property
    def item_code(self) -> str:
        return self.__item_code
    @item_code.setter
    def item_code(self, valor: str):
        self.__item_code = valor or ''

    @property
    def descripcion(self) -> str:
        return self.__descripcion
    @descripcion.setter
    def descripcion(self, valor: str):
        self.__descripcion = valor or ''

    @property
    def cantidad_pedida(self) -> float:
        return self.__cantidad_pedida
    @cantidad_pedida.setter
    def cantidad_pedida(self, valor: float):
        if valor < 0:
            raise ValueError("cantidad_pedida debe ser >= 0")
        self.__cantidad_pedida = float(valor)

    @property
    def cantidad_recibida(self) -> float:
        return self.__cantidad_recibida
    @cantidad_recibida.setter
    def cantidad_recibida(self, valor: float):
        if valor < 0:
            raise ValueError("cantidad_recibida debe ser >= 0")
        self.__cantidad_recibida = float(valor)

    @property
    def fecha_vencimiento(self) -> Optional[str]:
        return self.__fecha_vencimiento
    @fecha_vencimiento.setter
    def fecha_vencimiento(self, valor: Optional[str]):
        self.__fecha_vencimiento = valor

    @property
    def unidad_med(self) -> Optional[int]:
        return self.__unidad_med
    @unidad_med.setter
    def unidad_med(self, valor: Optional[int]):
        self.__unidad_med = valor if (valor is None or valor > 0) else None

    # ---------------------------
    # Serialización a dict
    # ---------------------------
    def to_dict(self):
        return {
            'item_code': self.item_code,
            'descripcion': self.descripcion,
            'cantidad_pedida': self.cantidad_pedida,
            'cantidad_recibida': self.cantidad_recibida,
            'fecha_vencimiento': self.fecha_vencimiento,
            'unidad_med': self.unidad_med
        }
