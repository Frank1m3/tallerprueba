from flask import Blueprint, render_template
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from datetime import date

solmod = Blueprint('solmod', __name__, template_folder='templates')


@solmod.route('/solicitud-index')
def solicitud_index():
    dao = SolicitudCompraDao()
    solicitudes = dao.obtener_solicitudes()
    return render_template('solicitud_index.html', solicitudes=solicitudes)


@solmod.route('/solicitudes/modificar/<int:id>')
def solicitud_modificar(id):
    dao = SolicitudCompraDao()
    solicitud = dao.obtener_solicitud_por_id(id)
    productos = dao.obtener_productos()
    return render_template('solicitud_modificar.html', solicitud=solicitud, productos=productos)


@solmod.route('/solicitud-agregar')
def solicitud_agregar():
    sdao = SucursalDao()
    fdao = FuncionarioDao()
    dao = SolicitudCompraDao()

    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    productos = dao.obtener_productos()
    fecha_actual = date.today().strftime("%Y-%m-%d")

    return render_template(
        'solicitud_agregar.html',
        sucursales=sucursales,
        funcionarios=funcionarios,
        productos=productos,
        fecha_actual=fecha_actual
    )
