from flask import Blueprint, render_template
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.proveedor.ProveedorDao import ProveedorDao
from app.dao.gestionar_compras.registrar_orden_compras.orden_de_compras_dao import OrdenDeComprasDao

ocmod = Blueprint('ocmod', __name__, template_folder='templates')


# ==============================
# Listado de órdenes
# ==============================
@ocmod.route('/ordenes-index')
def ordenes_index():
    return render_template('ordenes-index.html')


# ==============================
# Agregar orden
# ==============================
@ocmod.route('/ordenes-agregar')
def ordenes_agregar():
    sdao = SucursalDao()
    fdao = FuncionarioDao()
    provdao = ProveedorDao()
    ocdao = OrdenDeComprasDao()

    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    proveedores = provdao.getProveedores()
    # Items desde la tabla item (no usamos ProductoDao, que apunta a productos_legacy)
    productos = ocdao.obtener_productos()

    return render_template(
        'ordenes-agregar.html',
        sucursales=sucursales,
        funcionarios=funcionarios,
        proveedores=proveedores,
        productos=productos
    )


# ==============================
# Detalle de una orden
# ==============================
@ocmod.route('/ordenes/detalle/<int:id_orden>')
def ordenes_detalle(id_orden):
    dao = OrdenDeComprasDao()
    orden = dao.obtener_orden_por_id(id_orden)
    if not orden:
        return "Orden no encontrada", 404
    return render_template('detalle.html', orden=orden)
