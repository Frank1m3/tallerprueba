from typing import Optional

class SolicitudDetalleDto:
    """
    DTO para el detalle de una solicitud de compra.
    Representa cada ítem solicitado junto con cantidad, stock y precio.
    """

    def __init__(
        self,
        id_solicitud_cab: Optional[int] = None,
        id_item: int = None,
        item_descripcion: str = '',
        unidad_med: Optional[int] = None,
        cant_solicitada: float = 1.0,
        stock: float = 0.0,
        precio: float = 0.0
    ):
        self.__id_solicitud_cab = id_solicitud_cab
        self.__id_item = id_item
        self.__item_descripcion = item_descripcion
        self.__unidad_med = unidad_med
        self.__cant_solicitada = cant_solicitada
        self.__stock = stock
        self.__precio = precio

    @property
    def id_solicitud_cab(self) -> Optional[int]:
        return self.__id_solicitud_cab
    @id_solicitud_cab.setter
    def id_solicitud_cab(self, valor: int):
        self.__id_solicitud_cab = valor

    @property
    def id_item(self) -> int:
        return self.__id_item
    @id_item.setter
    def id_item(self, valor: int):
        if valor is None:
            raise ValueError("El id_item no puede estar vacío")
        self.__id_item = valor

    @property
    def item_descripcion(self) -> str:
        return self.__item_descripcion
    @item_descripcion.setter
    def item_descripcion(self, valor: str):
        if not valor:
            raise ValueError("La descripción no puede estar vacía")
        self.__item_descripcion = valor

    @property
    def unidad_med(self) -> Optional[int]:
        return self.__unidad_med
    @unidad_med.setter
    def unidad_med(self, valor: Optional[int]):
        if valor is not None and (not isinstance(valor, int) or valor <= 0):
            raise ValueError("unidad_med debe ser un entero positivo o None")
        self.__unidad_med = valor

    @property
    def cant_solicitada(self) -> float:
        return self.__cant_solicitada
    @cant_solicitada.setter
    def cant_solicitada(self, valor: float):
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ValueError("cant_solicitada debe ser un número positivo")
        self.__cant_solicitada = valor

    @property
    def cantidad(self) -> float:
        """Alias para compatibilidad con DAO."""
        return self.__cant_solicitada

    @property
    def stock(self) -> float:
        return self.__stock
    @stock.setter
    def stock(self, valor: float):
        if not isinstance(valor, (int, float)) or valor < 0:
            raise ValueError("stock debe ser un número >= 0")
        self.__stock = valor

    @property
    def precio(self) -> float:
        return self.__precio
    @precio.setter
    def precio(self, valor: float):
        if not isinstance(valor, (int, float)) or valor < 0:
            raise ValueError("precio debe ser un número >= 0")
        self.__precio = valor
