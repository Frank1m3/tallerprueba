from datetime import date, datetime
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app import csrf
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

scapi = Blueprint('scapi', __name__, url_prefix='/api/v1/gestionar-compras/registrar-solicitud-compras')

# ================================
# Siguiente número
# ================================
@scapi.route('/siguiente-nro-solicitud', methods=['GET'])
def siguiente_nro_solicitud():
    try:
        dao = SolicitudCompraDao()
        return jsonify({'success': True, 'siguiente_nro': dao.obtener_siguiente_nro_solicitud()})
    except Exception as e:
        app.logger.error(f"Error al obtener siguiente nro_solicitud: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# Funcionarios
# ================================
@scapi.route('/funcionarios', methods=['GET'])
def get_funcionarios():
    try:
        dao = FuncionarioDao()
        return jsonify({'success': True, 'data': dao.get_funcionarios(), 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener funcionarios: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Productos (todos los activos). Filtro opcional de stock por sucursal/deposito.
# ================================
@scapi.route('/productos', methods=['GET'])
def get_productos():
    try:
        dao = SolicitudCompraDao()
        id_sucursal = request.args.get('id_sucursal', type=int)
        id_deposito = request.args.get('id_deposito', type=int)
        productos = dao.obtener_productos(id_sucursal=id_sucursal, id_deposito=id_deposito)
        data = [{
            'id_item': p['id_item'],
            'item_code': p['item_code'],
            'nombre': p['nombre_producto'],
            'stock': p['stock'],
            'precio': p.get('precio', 0),
            'unidad_med': p.get('unidad_med', 1)
        } for p in productos]
        return jsonify({'success': True, 'data': data, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener productos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Depósitos de una sucursal
# ================================
@scapi.route('/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def get_sucursal_depositos(id_sucursal):
    try:
        dao = SucursalDao()
        return jsonify({'success': True, 'data': dao.get_sucursal_depositos(id_sucursal), 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Listado
# ================================
@scapi.route('/solicitudes', methods=['GET'])
def get_solicitudes():
    try:
        dao = SolicitudCompraDao()
        return jsonify({'success': True, 'data': dao.obtener_solicitudes()})
    except Exception as e:
        app.logger.error(f"Error al obtener solicitudes: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)}), 500

# ================================
# Crear (sin proveedor)
# ================================
@scapi.route('/solicitudes', methods=['POST'])
@csrf.exempt
def crear_solicitud():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        detalle_objs = [SolicitudDetalleDto(
            id_item=d.get('id_item'),
            item_descripcion=d.get('item_descripcion', ''),
            unidad_med=d.get('unidad_med', 1),
            cant_solicitada=d.get('cant_solicitada', 1),
            stock=d.get('stock', 0),
            precio=d.get('precio', 0)
        ) for d in data.get('detalle_solicitud', [])]

        fecha_raw = data.get('fecha_solicitud')
        if isinstance(fecha_raw, str):
            fecha_solicitud = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
        else:
            fecha_solicitud = fecha_raw or date.today()

        solicitud_dto = SolicitudDto(
            fecha_solicitud=fecha_solicitud,
            id_sucursal=data.get('id_sucursal'),
            id_deposito=data.get('id_deposito'),
            id_funcionario=data.get('id_funcionario'),
            detalle_solicitud=detalle_objs
        )

        dao = SolicitudCompraDao()
        if dao.agregar(solicitud_dto):
            return jsonify({'success': True, 'data': None, 'error': None}), 201
        return jsonify({'success': False, 'error': 'No se pudo registrar la solicitud'}), 500
    except Exception as e:
        app.logger.error(f"Error al crear solicitud: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Modificar
# ================================
@scapi.route('/modificar/<int:id_solicitud>', methods=['PUT'])
@csrf.exempt
def modificar_solicitud_api(id_solicitud):
    try:
        data = request.get_json()
        if not data or 'detalle_solicitud' not in data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        detalle_objs = [SolicitudDetalleDto(
            id_item=d.get('id_item'),
            cant_solicitada=d.get('cant_solicitada', 1)
        ) for d in data['detalle_solicitud']]

        cabecera = data.get('cabecera')
        if cabecera and 'fecha_solicitud' in cabecera:
            fecha_raw = cabecera['fecha_solicitud']
            if isinstance(fecha_raw, str):
                cabecera['fecha_solicitud'] = datetime.strptime(fecha_raw, "%Y-%m-%d").date()

        dao = SolicitudCompraDao()
        if dao.modificar_solicitud(id_solicitud, detalle_objs, cabecera):
            return jsonify({'success': True, 'message': 'Solicitud modificada correctamente'}), 200
        return jsonify({'success': False, 'error': 'No se pudo modificar la solicitud'}), 400
    except Exception as e:
        app.logger.error(f"Error al modificar solicitud {id_solicitud}: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Anular
# ================================
@scapi.route('/anular/<int:id_solicitud>', methods=['PUT'])
@csrf.exempt
def anular_solicitud(id_solicitud):
    try:
        dao = SolicitudCompraDao()
        if dao.anular(id_solicitud):
            return jsonify({'success': True, 'message': 'Solicitud anulada correctamente'}), 200
        return jsonify({'success': False, 'error': 'No se pudo anular la solicitud'}), 400
    except Exception as e:
        app.logger.error(f"Error al anular solicitud: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500
