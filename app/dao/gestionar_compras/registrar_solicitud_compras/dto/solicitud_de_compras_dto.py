from typing import List, Optional
from datetime import date
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto


class SolicitudDto:
    """
    DTO principal de la solicitud de compra.
    Contiene la cabecera y la lista de detalles.
    """

    def __init__(
        self,
        id_solicitud_cab: Optional[int] = None,
        nro_solicitud: str = '',
        id_funcionario: int = 0,
        id_sucursal: Optional[int] = None,
        id_deposito: Optional[int] = None,
        id_proveedor: Optional[int] = None,   # NUEVO CAMPO
        fecha_solicitud: Optional[date] = None,
        detalle_solicitud: Optional[List[SolicitudDetalleDto]] = None
    ):
        self.__id_solicitud_cab = id_solicitud_cab
        self.__nro_solicitud = nro_solicitud or f'SOL-{int(date.today().strftime("%Y%m%d"))}'
        self.__id_funcionario = id_funcionario
        self.__id_sucursal = id_sucursal
        self.__id_deposito = id_deposito
        self.__id_proveedor = id_proveedor
        self.__fecha_solicitud = fecha_solicitud or date.today()
        self.__detalle_solicitud = detalle_solicitud or []

    # --------------------
    # Propiedades
    # --------------------
    @property
    def id_solicitud_cab(self) -> Optional[int]:
        return self.__id_solicitud_cab

    @id_solicitud_cab.setter
    def id_solicitud_cab(self, valor: int):
        self.__id_solicitud_cab = valor

    @property
    def nro_solicitud(self) -> str:
        return self.__nro_solicitud

    @nro_solicitud.setter
    def nro_solicitud(self, valor: str):
        if not valor:
            raise ValueError("El atributo nro_solicitud no puede estar vacío")
        self.__nro_solicitud = valor

    @property
    def id_funcionario(self) -> int:
        return self.__id_funcionario

    @id_funcionario.setter
    def id_funcionario(self, valor: int):
        if not valor:
            raise ValueError("El atributo id_funcionario no puede estar vacío")
        self.__id_funcionario = valor

    @property
    def id_sucursal(self) -> Optional[int]:
        return self.__id_sucursal

    @id_sucursal.setter
    def id_sucursal(self, valor: Optional[int]):
        self.__id_sucursal = valor

    @property
    def id_deposito(self) -> Optional[int]:
        return self.__id_deposito

    @id_deposito.setter
    def id_deposito(self, valor: Optional[int]):
        self.__id_deposito = valor

    @property
    def id_proveedor(self) -> Optional[int]:
        return self.__id_proveedor

    @id_proveedor.setter
    def id_proveedor(self, valor: Optional[int]):
        self.__id_proveedor = valor

    @property
    def fecha_solicitud(self) -> date:
        return self.__fecha_solicitud

    @fecha_solicitud.setter
    def fecha_solicitud(self, valor: date):
        if not isinstance(valor, date):
            raise ValueError("El atributo fecha_solicitud debe ser de tipo 'date'")
        self.__fecha_solicitud = valor

    @property
    def detalle_solicitud(self) -> List[SolicitudDetalleDto]:
        return self.__detalle_solicitud

    @detalle_solicitud.setter
    def detalle_solicitud(self, detalle_solicitud: List[SolicitudDetalleDto]):
        if not isinstance(detalle_solicitud, list):
            raise ValueError("detalle_solicitud debe ser una lista de objetos SolicitudDetalleDto")
        for item in detalle_solicitud:
            if not isinstance(item, SolicitudDetalleDto):
                raise ValueError("Todos los elementos de detalle_solicitud deben ser instancias de SolicitudDetalleDto")
        self.__detalle_solicitud = detalle_solicitud
