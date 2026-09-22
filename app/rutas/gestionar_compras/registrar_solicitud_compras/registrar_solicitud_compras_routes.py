from flask import Blueprint, render_template, flash, redirect, url_for
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
    if not solicitud:
        flash('La solicitud no existe.', 'danger')
        return redirect(url_for('solmod.solicitud_index'))
    if solicitud['estado'] != 'PENDIENTE':
        flash(f"Solo se puede modificar una solicitud en estado PENDIENTE (esta está {solicitud['estado']}).", 'warning')
        return redirect(url_for('solmod.solicitud_index'))
    return render_template('solicitud_modificar.html', solicitud=solicitud)


@solmod.route('/solicitud-agregar')
def solicitud_agregar():
    sdao = SucursalDao()
    fdao = FuncionarioDao()

    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    fecha_actual = date.today().strftime("%Y-%m-%d")

    return render_template(
        'solicitud_agregar.html',
        sucursales=sucursales,
        funcionarios=funcionarios,
        fecha_actual=fecha_actual
    )
