from typing import List, Optional
from datetime import date
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto
from app.dao.referenciales.estado_pedido_compra.estado_pedido_compra_dto import EstadoPedidoCompra

class PedidoDeComprasDto:

    def __init__(
        self,
        id_pedido_compra_cab: Optional[int] = None,
        nro_pedido: str = '',
        nro_solicitud: Optional[str] = None,
        id_funcionario: int = 0,
        id_proveedor: Optional[int] = None,
        id_sucursal: Optional[int] = None,
        id_deposito: Optional[int] = None,
        estado: Optional[EstadoPedidoCompra] = None,
        fecha_pedido: Optional[date] = None,
        fecha_necesaria: Optional[date] = None,
        detalle_pedido: Optional[List[PedidoDeCompraDetalleDto]] = None,
        tipo_factura: Optional[str] = None
    ):
        if id_proveedor is None:
            raise ValueError("El id_proveedor no puede ser None al crear un pedido")
        if id_funcionario == 0:
            raise ValueError("El id_funcionario no puede ser 0 al crear un pedido")

        self.__id_pedido_compra_cab = id_pedido_compra_cab
        self.__nro_pedido = nro_pedido or f'PED-{int(date.today().strftime("%Y%m%d"))}'
        self.__nro_solicitud = nro_solicitud
        self.__id_funcionario = id_funcionario
        self.__id_proveedor = id_proveedor
        self.__id_sucursal = id_sucursal
        self.__id_deposito = id_deposito
        self.__estado = estado
        self.__fecha_pedido = fecha_pedido or date.today()
        self.__fecha_necesaria = fecha_necesaria
        self.__detalle_pedido = detalle_pedido or []
        self.tipo_factura = tipo_factura  # queda como atributo público opcional

    # --------------------
    # Propiedades
    # --------------------
    @property
    def id_pedido_compra_cab(self) -> Optional[int]:
        return self.__id_pedido_compra_cab

    @id_pedido_compra_cab.setter
    def id_pedido_compra_cab(self, valor: int):
        self.__id_pedido_compra_cab = valor

    @property
    def nro_pedido(self) -> str:
        return self.__nro_pedido

    @nro_pedido.setter
    def nro_pedido(self, valor: str):
        if not valor:
            raise ValueError("El atributo nro_pedido no puede estar vacío")
        self.__nro_pedido = valor

    @property
    def nro_solicitud(self) -> Optional[str]:
        return self.__nro_solicitud

    @nro_solicitud.setter
    def nro_solicitud(self, valor: Optional[str]):
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
    def id_proveedor(self) -> int:
        return self.__id_proveedor

    @id_proveedor.setter
    def id_proveedor(self, valor: int):
        if valor is None:
            raise ValueError("El atributo id_proveedor no puede ser None")
        self.__id_proveedor = valor

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
    def estado(self) -> Optional[EstadoPedidoCompra]:
        return self.__estado

    @estado.setter
    def estado(self, valor: EstadoPedidoCompra):
        if valor is not None and not isinstance(valor, EstadoPedidoCompra):
            raise ValueError("El atributo estado debe ser de tipo 'EstadoPedidoCompra'")
        self.__estado = valor

    @property
    def fecha_pedido(self) -> date:
        return self.__fecha_pedido

    @fecha_pedido.setter
    def fecha_pedido(self, valor: date):
        if not isinstance(valor, date):
            raise ValueError("El atributo fecha_pedido debe ser de tipo 'date'")
        self.__fecha_pedido = valor

    @property
    def fecha_necesaria(self) -> Optional[date]:
        return self.__fecha_necesaria

    @fecha_necesaria.setter
    def fecha_necesaria(self, valor: Optional[date]):
        if valor is not None and not isinstance(valor, date):
            raise ValueError("El atributo fecha_necesaria debe ser de tipo 'date'")
        self.__fecha_necesaria = valor

    @property
    def detalle_pedido(self) -> List[PedidoDeCompraDetalleDto]:
        return self.__detalle_pedido

    @detalle_pedido.setter
    def detalle_pedido(self, detalle_pedido: List[PedidoDeCompraDetalleDto]):
        if not isinstance(detalle_pedido, list):
            raise ValueError("detalle_pedido debe ser una lista de objetos PedidoDeCompraDetalleDto")
        for item in detalle_pedido:
            if not isinstance(item, PedidoDeCompraDetalleDto):
                raise ValueError("Todos los elementos de detalle_pedido deben ser instancias de PedidoDeCompraDetalleDto")
        self.__detalle_pedido = detalle_pedido
