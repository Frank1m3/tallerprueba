class ProductoDto:

    def __init__(self, id_producto, nombre, cantidad=None, precio_unitario=None,
                 item_code='', id_proveedor=None, proveedor_nombre=''):
        self.__id_producto = id_producto
        self.__nombre = nombre
        self.__cantidad = cantidad
        self.__precio_unitario = precio_unitario
        self.__item_code = item_code
        self.__id_proveedor = id_proveedor
        self.__proveedor_nombre = proveedor_nombre

    # Getters y setters
    @property
    def id_producto(self):
        return self.__id_producto

    @id_producto.setter
    def id_producto(self, valor):
        if not valor:
            raise ValueError("El atributo id_producto no puede estar vacío")
        self.__id_producto = valor

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not valor:
            raise ValueError("El atributo nombre no puede estar vacío")
        self.__nombre = valor.upper()

    @property
    def cantidad(self):
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor):
        self.__cantidad = valor

    @property
    def precio_unitario(self):
        return self.__precio_unitario

    @precio_unitario.setter
    def precio_unitario(self, valor):
        self.__precio_unitario = valor

    @property
    def item_code(self):
        return self.__item_code

    @item_code.setter
    def item_code(self, valor):
        self.__item_code = valor

    @property
    def id_proveedor(self):
        return self.__id_proveedor

    @id_proveedor.setter
    def id_proveedor(self, valor):
        self.__id_proveedor = valor

    @property
    def proveedor_nombre(self):
        return self.__proveedor_nombre

    @proveedor_nombre.setter
    def proveedor_nombre(self, valor):
        self.__proveedor_nombre = valor
