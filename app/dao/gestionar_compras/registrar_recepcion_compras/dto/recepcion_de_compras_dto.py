from typing import List, Optional
from datetime import date
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compra_detalle_dto import RecepcionDetalleDto

class RecepcionDto:
    """
    DTO para la cabecera de una recepción de mercadería.
    Incluye información de cabecera y lista de detalles.
    """

    def __init__(
        self,
        id_recepcion_cab: Optional[int] = None,
        nro_recepcion: Optional[str] = None,
        id_funcionario: Optional[int] = None,
        id_sucursal: Optional[int] = None,
        id_deposito: Optional[int] = None,
        id_proveedor: Optional[int] = None,
        fecha_recepcion: Optional[date] = None,
        detalle_recepcion: Optional[List[RecepcionDetalleDto]] = None,
        id_pedido: Optional[int] = None  # vincula el pedido
    ):
        self.__id_recepcion_cab = id_recepcion_cab
        self.__nro_recepcion = nro_recepcion or f'REC-{int(date.today().strftime("%Y%m%d"))}'
        self.__id_funcionario = id_funcionario or 0
        self.__id_sucursal = id_sucursal
        self.__id_deposito = id_deposito
        self.__id_proveedor = id_proveedor
        self.__fecha_recepcion = fecha_recepcion or date.today()
        self.__detalle_recepcion = detalle_recepcion or []
        self.__id_pedido = id_pedido

    # ---------------------------
    # Propiedades
    # ---------------------------
    @property
    def id_recepcion_cab(self) -> Optional[int]:
        return self.__id_recepcion_cab
    @id_recepcion_cab.setter
    def id_recepcion_cab(self, valor: int):
        self.__id_recepcion_cab = valor

    @property
    def nro_recepcion(self) -> str:
        return self.__nro_recepcion
    @nro_recepcion.setter
    def nro_recepcion(self, valor: str):
        self.__nro_recepcion = valor or self.__nro_recepcion

    @property
    def id_funcionario(self) -> int:
        return self.__id_funcionario
    @id_funcionario.setter
    def id_funcionario(self, valor: int):
        self.__id_funcionario = valor or 0

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
    def fecha_recepcion(self) -> date:
        return self.__fecha_recepcion
    @fecha_recepcion.setter
    def fecha_recepcion(self, valor: date):
        self.__fecha_recepcion = valor if isinstance(valor, date) else date.today()

    @property
    def detalle_recepcion(self) -> List[RecepcionDetalleDto]:
        return self.__detalle_recepcion
    @detalle_recepcion.setter
    def detalle_recepcion(self, detalle_recepcion: List[RecepcionDetalleDto]):
        self.__detalle_recepcion = detalle_recepcion or []

    @property
    def id_pedido(self) -> Optional[int]:
        return self.__id_pedido
    @id_pedido.setter
    def id_pedido(self, valor: Optional[int]):
        self.__id_pedido = valor

    # ---------------------------
    # Serialización a dict
    # ---------------------------
    def to_dict(self):
        return {
            'id_recepcion_cab': self.id_recepcion_cab,
            'nro_recepcion': self.nro_recepcion,
            'id_funcionario': self.id_funcionario,
            'id_sucursal': self.id_sucursal,
            'id_deposito': self.id_deposito,
            'id_proveedor': self.id_proveedor,
            'fecha_recepcion': self.fecha_recepcion.isoformat(),
            'detalle_recepcion': [d.to_dict() for d in self.detalle_recepcion],
            'id_pedido': self.id_pedido
        }
