from typing import Optional

class PresupuestoCompraDetalleDto:
    """
    Representa cada ítem del detalle de un presupuesto de compra.
    """
    def __init__(
        self,
        id_pre_compra_det: Optional[int] = None,
        id_pre_compra_cab: Optional[int] = None,
        item_code: str = '',
        cantidad: float = 0.0,
        precio_unitario: float = 0.0
    ):
        self.__id_pre_compra_det = id_pre_compra_det
        self.__id_pre_compra_cab = id_pre_compra_cab
        self.item_code = item_code
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    @property
    def id_pre_compra_det(self) -> Optional[int]:
        return self.__id_pre_compra_det

    @property
    def id_pre_compra_cab(self) -> Optional[int]:
        return self.__id_pre_compra_cab

    @property
    def item_code(self) -> str:
        return self.__item_code

    @item_code.setter
    def item_code(self, valor: str):
        if not valor:
            raise ValueError("item_code no puede estar vacío")
        self.__item_code = valor

    @property
    def cantidad(self) -> float:
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: float):
        if valor is None or valor <= 0:
            raise ValueError("cantidad debe ser un número positivo")
        self.__cantidad = valor

    @property
    def precio_unitario(self) -> float:
        return self.__precio_unitario

    @precio_unitario.setter
    def precio_unitario(self, valor: float):
        if valor is None or valor < 0:
            raise ValueError("precio_unitario debe ser un número no negativo")
        self.__precio_unitario = valor
