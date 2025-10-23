from flask import Blueprint, render_template, jsonify, current_app as app
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.producto.ProductoDao import ProductoDao
from app.dao.gestionar_compras.registrar_pedido_compras.pedido_de_compras_dao import PedidoDeComprasDao
from app.dao.referenciales.proveedor.ProveedorDao import ProveedorDao

pdcmod = Blueprint('pdcmod', __name__, template_folder='templates')


# ==============================
# Vista de listado de pedidos
# ==============================
@pdcmod.route('/pedidos-index')
def pedidos_index():
    dao = PedidoDeComprasDao() 
    pedidos = dao.obtener_pedidos()
    return render_template('pedidos-index.html', pedidos=pedidos)


# ==============================
# Vista para agregar un pedido
# ==============================
@pdcmod.route('/pedidos-agregar')
def pedidos_agregar():
    # Instanciamos los DAOs
    sdao = SucursalDao()
    empdao = FuncionarioDao()
    pdao = ProductoDao()
    provdao = ProveedorDao()

    # Listas referenciales para los selects
    sucursales = sdao.getSucursales()
    funcionarios = empdao.get_funcionarios()
    proveedores = provdao.getProveedores()
    productos = pdao.get_productos()

    # Renderizamos la plantilla
    return render_template(
        'pedidos-agregar.html',
        sucursales=sucursales,
        funcionarios=funcionarios,
        proveedores=proveedores,
        productos=productos
    )


# ==============================
# Endpoint para obtener proveedores vía AJAX
# ==============================
@pdcmod.route('/proveedores', methods=['GET'])
def get_proveedores():
    try:
        dao = ProveedorDao()
        proveedores = dao.getProveedores()
        return jsonify({'success': True, 'data': proveedores, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener proveedores: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500


# ==============================
# Vista para ver detalle de un pedido
# ==============================
@pdcmod.route('/pedidos/detalle/<int:id_pedido>')
def pedidos_detalle(id_pedido):
    dao = PedidoDeComprasDao()
    pedido = dao.obtener_pedido_por_id(id_pedido)  # Debe traer el diccionario completo con detalle
    if not pedido:
        return "Pedido no encontrado", 404
    return render_template('detalle.html', pedido=pedido)
