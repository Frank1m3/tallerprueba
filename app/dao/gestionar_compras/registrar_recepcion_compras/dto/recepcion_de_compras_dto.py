from typing import List, Optional
from datetime import date
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compra_detalle_dto import RecepcionDetalleDto
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes

class RecepcionDto:
    """Cabecera de recepción de mercadería vinculada a orden de compra."""

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
<<<<<<< Updated upstream
        id_pedido: Optional[int] = None  # nuevo campo para vincular el pedido
=======
        id_pedido: Optional[int] = None,
        id_orden_compra_cab: Optional[int] = None
>>>>>>> Stashed changes
    ):
        self.__id_recepcion_cab = id_recepcion_cab
        # Solo generar nro_recepcion si no se pasa ninguno
        self.__nro_recepcion = nro_recepcion or f'REC-{int(date.today().strftime("%Y%m%d"))}'
        self.__id_funcionario = id_funcionario or 0
        self.__id_sucursal = id_sucursal
        self.__id_deposito = id_deposito
        self.__id_proveedor = id_proveedor
        self.__fecha_recepcion = fecha_recepcion or date.today()
        self.__detalle_recepcion = detalle_recepcion or []
        self.__id_pedido = id_pedido
        self.__id_orden_compra_cab = id_orden_compra_cab

    @property
    def id_recepcion_cab(self) -> Optional[int]: 
        return self.__id_recepcion_cab
<<<<<<< Updated upstream
    @id_recepcion_cab.setter
    def id_recepcion_cab(self, valor: int): 
        self.__id_recepcion_cab = valor
=======
>>>>>>> Stashed changes

    @property
    def nro_recepcion(self) -> str: 
        return self.__nro_recepcion

    @property
    def id_funcionario(self) -> int: 
        return self.__id_funcionario

    @property
    def id_sucursal(self) -> Optional[int]: 
        return self.__id_sucursal
<<<<<<< Updated upstream
    @id_sucursal.setter
    def id_sucursal(self, valor: Optional[int]): 
        self.__id_sucursal = valor
=======
>>>>>>> Stashed changes

    @property
    def id_deposito(self) -> Optional[int]: 
        return self.__id_deposito
<<<<<<< Updated upstream
    @id_deposito.setter
    def id_deposito(self, valor: Optional[int]): 
        self.__id_deposito = valor
=======
>>>>>>> Stashed changes

    @property
    def id_proveedor(self) -> Optional[int]: 
        return self.__id_proveedor
<<<<<<< Updated upstream
    @id_proveedor.setter
    def id_proveedor(self, valor: Optional[int]): 
        self.__id_proveedor = valor
=======
>>>>>>> Stashed changes

    @property
    def fecha_recepcion(self) -> date: 
        return self.__fecha_recepcion

    @property
    def detalle_recepcion(self) -> List[RecepcionDetalleDto]: 
        return self.__detalle_recepcion

    @property
    def id_pedido(self) -> Optional[int]:
        return self.__id_pedido
<<<<<<< Updated upstream
    @id_pedido.setter
    def id_pedido(self, valor: Optional[int]):
        self.__id_pedido = valor
=======

    @property
    def id_orden_compra_cab(self) -> Optional[int]:
        return self.__id_orden_compra_cab

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
            'id_pedido': self.id_pedido,
            'id_orden_compra_cab': self.id_orden_compra_cab
        }
>>>>>>> Stashed changes
