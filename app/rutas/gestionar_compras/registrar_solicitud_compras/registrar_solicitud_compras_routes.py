from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.producto.ProductoDao import ProductoDao
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

solmod = Blueprint('solmod', __name__, template_folder='templates')

# ================================
# Listado de solicitudes
# ================================
@solmod.route('/solicitud-index')
def solicitud_index():
    dao = SolicitudCompraDao()
    solicitudes = dao.obtener_solicitudes()
    return render_template('solicitud_index.html', solicitudes=solicitudes)

# ================================
# Agregar nueva solicitud
# ================================
@solmod.route('/solicitud-agregar', methods=['GET', 'POST'])
def solicitud_agregar():
    sdao = SucursalDao()
    empdao = FuncionarioDao()
    pdao = ProductoDao()
    solicitud_dao = SolicitudCompraDao()

    if request.method == 'POST':
        id_sucursal = request.form.get('id_sucursal')
        id_deposito = request.form.get('id_deposito')
        id_solicitante = request.form.get('id_solicitante')
        fecha_solicitud = request.form.get('fecha_solicitud')

        detalle = []
        items = request.form.getlist('item_id[]')
        cantidades = request.form.getlist('cantidad[]')
        unidades = request.form.getlist('unidad[]')
        fechas_necesarias = request.form.getlist('fecha_necesaria[]')

        for i in range(len(items)):
            detalle.append(SolicitudDetalleDto(
                id_item=int(items[i]),
                cantidad=float(cantidades[i]),
                unidad_medida=int(unidades[i]),
                fecha_necesaria=fechas_necesarias[i]
            ))

        solicitud_dto = SolicitudCompraDto(
            fecha_solicitud=fecha_solicitud,
            id_sucursal=int(id_sucursal),
            id_deposito=int(id_deposito) if id_deposito else None,
            id_solicitante=int(id_solicitante),
            detalle_solicitud=detalle
        )

        exito = solicitud_dao.agregar(solicitud_dto)
        if exito:
            flash('Solicitud agregada correctamente', 'success')
            return redirect(url_for('solmod.solicitud_index'))
        else:
            flash('Error al agregar solicitud', 'danger')

    return render_template(
        'solicitud_agregar.html',
        sucursales=sdao.getSucursales(),
        funcionarios=empdao.get_funcionarios(),
        productos=pdao.get_productos()
    )
# ================================
# Obtener depósitos de una sucursal
# ================================
@solmod.route('/api/v1/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def get_sucursal_depositos(id_sucursal):
    try:
        sdao = SucursalDao()
        depositos = sdao.get_sucursal_depositos(id_sucursal)  # debe devolver lista de dicts
        # Asegurarse de que la salida tenga id_deposito y nombre_deposito
        lista = [{"id_deposito": d["id_deposito"], "nombre_deposito": d["descripcion"]} for d in depositos]
        return jsonify({"success": True, "data": lista, "error": None})
    except Exception as e:
        return jsonify({"success": False, "data": [], "error": str(e)})
