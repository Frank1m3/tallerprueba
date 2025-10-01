from flask import Blueprint, render_template
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.proveedor.ProveedorDao import ProveedorDao
from datetime import date

solmod = Blueprint('solmod', __name__, template_folder='templates')


# ==============================
# Listado de solicitudes
# ==============================
@solmod.route('/solicitud-index')
def solicitud_index():
    dao = SolicitudCompraDao()
    solicitudes = dao.obtener_solicitudes()
    return render_template('solicitud_index.html', solicitudes=solicitudes)


# ==============================
# Modificar solicitud
# ==============================
@solmod.route('/solicitudes/modificar/<int:id>')
def solicitud_modificar(id):
    dao = SolicitudCompraDao()
    sdao = SucursalDao()
    fdao = FuncionarioDao()
    pdao = ProveedorDao()

    # Obtener la solicitud
    solicitud = dao.obtener_solicitud_por_id(id)  # Este método debe devolver cabecera + detalles

    # Listas referenciales para selects
    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    proveedores = pdao.getProveedores()
    productos = dao.obtener_productos()  # Todos los productos activos

    return render_template(
        'solicitud_modificar.html',
        solicitud=solicitud,
        sucursales=sucursales,
        funcionarios=funcionarios,
        proveedores=proveedores,
        productos=productos
    )


# ==============================
# Agregar nueva solicitud
# ==============================
@solmod.route('/solicitud-agregar')
def solicitud_agregar():
    # DAOs referenciales
    sdao = SucursalDao()
    fdao = FuncionarioDao()
    pdao = ProveedorDao()
    dao = SolicitudCompraDao()

    # Obtener datos para los selects
    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    proveedores = pdao.getProveedores()
    productos = dao.obtener_productos()

    # Fecha actual para el input
    fecha_actual = date.today().strftime("%Y-%m-%d")

    return render_template(
        'solicitud_agregar.html',
        sucursales=sucursales,
        funcionarios=funcionarios,
        proveedores=proveedores,
        productos=productos,
        fecha_actual=fecha_actual
    )
