from typing import List, Optional
from datetime import date
from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_detalle_dto import PresupuestoCompraDetalleDto

class PresupuestoCompraDto:
    """
    DTO para la cabecera de presupuesto de compra.
    """
    def __init__(
        self,
        id_pre_compra_cab: Optional[int] = None,
        cod_presupuesto: str = '',
        fun_id: Optional[int] = None,
        id_proveedor: Optional[int] = None,
        id_sucursal: Optional[int] = None,   # <-- NUEVO CAMPO
        fecha_emision: Optional[date] = None,
        fecha_vencimiento: Optional[date] = None,
        condicion_compra: Optional[date] = None,
        estado: str = 'PENDIENTE',
        detalles: Optional[List[PresupuestoCompraDetalleDto]] = None,
        archivo: Optional[str] = None        # <-- Para guardar nombre/ruta del archivo
    ):
        self.__id_pre_compra_cab = id_pre_compra_cab
        self.cod_presupuesto = cod_presupuesto
        self.fun_id = fun_id
        self.id_proveedor = id_proveedor
        self.id_sucursal = id_sucursal
        self.fecha_emision = fecha_emision or date.today()
        self.fecha_vencimiento = fecha_vencimiento
        self.condicion_compra = condicion_compra
        self.estado = estado
        self.detalles = detalles or []
        self.archivo = archivo

    @property
    def id_pre_compra_cab(self) -> Optional[int]:
        return self.__id_pre_compra_cab

    @property
    def cod_presupuesto(self) -> str:
        return self.__cod_presupuesto

    @cod_presupuesto.setter
    def cod_presupuesto(self, valor: str):
        if not valor:
            raise ValueError("cod_presupuesto no puede estar vacío")
        self.__cod_presupuesto = valor

    @property
    def fun_id(self) -> Optional[int]:
        return self.__fun_id

    @fun_id.setter
    def fun_id(self, valor: Optional[int]):
        self.__fun_id = valor

    @property
    def id_proveedor(self) -> Optional[int]:
        return self.__id_proveedor

    @id_proveedor.setter
    def id_proveedor(self, valor: Optional[int]):
        self.__id_proveedor = valor

    @property
    def id_sucursal(self) -> Optional[int]:
        return self.__id_sucursal

    @id_sucursal.setter
    def id_sucursal(self, valor: Optional[int]):
        self.__id_sucursal = valor

    @property
    def fecha_emision(self) -> date:
        return self.__fecha_emision

    @fecha_emision.setter
    def fecha_emision(self, valor: date):
        self.__fecha_emision = valor

    @property
    def fecha_vencimiento(self) -> Optional[date]:
        return self.__fecha_vencimiento

    @fecha_vencimiento.setter
    def fecha_vencimiento(self, valor: Optional[date]):
        self.__fecha_vencimiento = valor

    @property
    def condicion_compra(self) -> Optional[date]:
        return self.__condicion_compra

    @condicion_compra.setter
    def condicion_compra(self, valor: Optional[date]):
        self.__condicion_compra = valor

    @property
    def estado(self) -> str:
        return self.__estado

    @estado.setter
    def estado(self, valor: str):
        if not valor:
            raise ValueError("estado no puede estar vacío")
        self.__estado = valor

    @property
    def detalles(self) -> List[PresupuestoCompraDetalleDto]:
        return self.__detalles

    @detalles.setter
    def detalles(self, valor: List[PresupuestoCompraDetalleDto]):
        if not isinstance(valor, list):
            raise ValueError("detalles debe ser una lista de PresupuestoCompraDetalleDto")
        self.__detalles = valor

    @property
    def archivo(self) -> Optional[str]:
        return self.__archivo

    @archivo.setter
    def archivo(self, valor: Optional[str]):
        self.__archivo = valor
