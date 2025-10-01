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
    funcionarios = fdao.get_funcionarios()       # [{'fun_id':..., 'nombre_completo':...}]
    proveedores = pdao.getProveedores()          # [{'id_proveedor':..., 'nombre':...}]
    productos = dao.obtener_productos()          # Lista de productos activos con stock y proveedor

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
