# DTO para el detalle de pedido de compras
class PedidoDeCompraDetalleDto:

    def __init__(
        self,
        id_pedido_compra_cab: int = None,
        id_item: int = None,
        item_code: str = '',
        item_descripcion: str = '',
        unidad_med: int = None,
        cant_pedido: float = 1.0,
        costo_unitario: float = 0.0,
        tipo_impuesto: str = None,
        id_proveedor: int = None,
        stock_actual: float = 0.0
    ):
        if id_item is None:
            raise ValueError("id_item no puede ser None")
        if not item_code:
            raise ValueError("item_code no puede estar vacío")
        if not item_descripcion:
            raise ValueError("item_descripcion no puede estar vacía")
        if id_proveedor is None:
            raise ValueError("id_proveedor no puede ser None")

        self.__id_pedido_compra_cab = id_pedido_compra_cab
        self.__id_item = id_item
        self.__item_code = item_code
        self.__item_descripcion = item_descripcion
        self.__unidad_med = unidad_med
        self.__cant_pedido = cant_pedido
        self.__costo_unitario = costo_unitario
        self.__tipo_impuesto = tipo_impuesto
        self.__id_proveedor = id_proveedor
        self.__stock_actual = stock_actual

    # --------------------
    # Propiedades
    # --------------------
    @property
    def id_pedido_compra_cab(self) -> int:
        return self.__id_pedido_compra_cab

    @id_pedido_compra_cab.setter
    def id_pedido_compra_cab(self, valor: int):
        self.__id_pedido_compra_cab = valor

    @property
    def id_item(self) -> int:
        return self.__id_item

    @id_item.setter
    def id_item(self, valor: int):
        if valor is None:
            raise ValueError("id_item no puede ser None")
        self.__id_item = valor

    @property
    def item_code(self) -> str:
        return self.__item_code

    @item_code.setter
    def item_code(self, valor: str):
        if not valor:
            raise ValueError("item_code no puede estar vacío")
        self.__item_code = valor

    @property
    def item_descripcion(self) -> str:
        return self.__item_descripcion

    @item_descripcion.setter
    def item_descripcion(self, valor: str):
        if not valor:
            raise ValueError("item_descripcion no puede estar vacía")
        self.__item_descripcion = valor

    @property
    def unidad_med(self) -> int:
        return self.__unidad_med

    @unidad_med.setter
    def unidad_med(self, valor: int):
        if valor is not None and (not isinstance(valor, int) or valor <= 0):
            raise ValueError("unidad_med debe ser un entero positivo o None")
        self.__unidad_med = valor

    @property
    def cant_pedido(self) -> float:
        return self.__cant_pedido

    @cant_pedido.setter
    def cant_pedido(self, valor: float):
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ValueError("cant_pedido debe ser un número positivo")
        self.__cant_pedido = valor

    @property
    def costo_unitario(self) -> float:
        return self.__costo_unitario

    @costo_unitario.setter
    def costo_unitario(self, valor: float):
        if not isinstance(valor, (int, float)) or valor < 0:
            raise ValueError("costo_unitario debe ser un número no negativo")
        self.__costo_unitario = valor

    @property
    def tipo_impuesto(self) -> str:
        return self.__tipo_impuesto

    @tipo_impuesto.setter
    def tipo_impuesto(self, valor: str):
        self.__tipo_impuesto = valor

    @property
    def id_proveedor(self) -> int:
        return self.__id_proveedor

    @id_proveedor.setter
    def id_proveedor(self, valor: int):
        if valor is None:
            raise ValueError("id_proveedor no puede ser None")
        self.__id_proveedor = valor

    @property
    def stock_actual(self) -> float:
        return self.__stock_actual

    @stock_actual.setter
    def stock_actual(self, valor: float):
        if not isinstance(valor, (int, float)) or valor < 0:
            raise ValueError("stock_actual debe ser un número no negativo")
        self.__stock_actual = valor
