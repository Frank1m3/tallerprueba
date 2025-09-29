from flask import Blueprint, render_template
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.producto.ProductoDao import ProductoDao
from app.dao.gestionar_compras.registrar_pedido_compras.pedido_de_compras_dao import PedidoDeComprasDao


pdcmod = Blueprint('pdcmod', __name__, template_folder='templates')


@pdcmod.route('/pedidos-index')
def pedidos_index():
    dao = PedidoDeComprasDao() 
    pedidos = dao.obtener_pedidos()
    return render_template('pedidos-index.html', pedidos=pedidos)


@pdcmod.route('/pedidos-agregar')
def pedidos_agregar():
    sdao = SucursalDao()
    empdao = FuncionarioDao()
    pdao = ProductoDao()

    # Corregido: llamar al método correcto del DAO
    return render_template(
    'pedidos-agregar.html',
    sucursales=sdao.getSucursales(),
    funcionarios=empdao.get_funcionarios(),  # coincida con el template
    productos=pdao.get_productos()
)

