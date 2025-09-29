from datetime import date, datetime
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app import csrf

from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

scapi = Blueprint('scapi', __name__)

# ================================
# Obtener siguiente número de solicitud
# ================================
@scapi.route('/siguiente-nro-solicitud', methods=['GET'])
def siguiente_nro_solicitud():
    try:
        dao = SolicitudCompraDao()
        siguiente = dao.obtener_siguiente_nro_solicitud()
        return jsonify(success=True, siguiente_nro=siguiente)
    except Exception as e:
        app.logger.error(f"Error al obtener siguiente nro_solicitud: {str(e)}")
        return jsonify(success=False, error=str(e)), 500

# ================================
# Obtener funcionarios activos
# ================================
@scapi.route('/funcionarios', methods=['GET'])
def get_funcionarios():
    try:
        dao = FuncionarioDao()
        funcionarios = dao.get_funcionarios()
        return jsonify({'success': True, 'data': funcionarios, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener funcionarios: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener productos (solo id y descripción)
# ================================
@scapi.route('/productos', methods=['GET'])
def get_productos():
    try:
        dao = SolicitudCompraDao()
        id_sucursal = request.args.get('id_sucursal', type=int)
        id_deposito = request.args.get('id_deposito', type=int)
        productos = dao.obtener_productos(id_sucursal=id_sucursal, id_deposito=id_deposito)
        # Eliminar stock y proveedor
        productos = [{'id_item': p['id_item'], 'nombre': p['nombre']} for p in productos]
        return jsonify({'success': True, 'data': productos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener productos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener depósitos de una sucursal
# ================================
@scapi.route('/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def get_sucursal_depositos(id_sucursal):
    try:
        dao = SolicitudCompraDao()
        depositos = dao.obtener_depositos_por_sucursal(id_sucursal)
        return jsonify({'success': True, 'data': depositos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener todas las solicitudes
# ================================
@scapi.route('/solicitudes', methods=['GET'])
def get_solicitudes():
    try:
        dao = SolicitudCompraDao()
        solicitudes = dao.obtener_solicitudes()
        return jsonify({'success': True, 'data': solicitudes})
    except Exception as e:
        app.logger.error(f"Error al obtener solicitudes: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)}), 500

# ================================
# Crear nueva solicitud
# ================================
@scapi.route('/solicitudes', methods=['POST'])
@csrf.exempt
def crear_solicitud():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        # Crear objetos de detalle usando id_item
        detalle_objs = []
        for d in data.get('detalle_solicitud', []):
            detalle_objs.append(
                SolicitudDetalleDto(
                    id_item=d.get('id_item'),
                    item_descripcion=d.get('item_descripcion', ''),
                    unidad_med=d.get('unidad_med', None),
                    cant_solicitada=d.get('cantidad', 1.0)
                )
            )

        # Convertir fecha si viene como string
        fecha_raw = data.get('fecha_solicitud')
        if isinstance(fecha_raw, str):
            try:
                fecha_solicitud = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
            except ValueError:
                fecha_solicitud = date.today()
        else:
            fecha_solicitud = fecha_raw or date.today()

        # Crear DTO principal
        solicitud_dto = SolicitudDto(
            fecha_solicitud=fecha_solicitud,
            id_sucursal=data.get('id_sucursal'),
            id_deposito=data.get('id_deposito'),
            id_funcionario=data.get('id_funcionario'),
            detalle_solicitud=detalle_objs
        )

        dao = SolicitudCompraDao()
        exito = dao.agregar(solicitud_dto)
        if exito:
            return jsonify({'success': True, 'data': None, 'error': None}), 201
        else:
            return jsonify({'success': False, 'error': 'No se pudo registrar la solicitud'}), 500

    except Exception as e:
        app.logger.error(f"Error al crear solicitud: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500
# ================================
# Anular una solicitud
# ================================
@scapi.route('/anular/<int:id_solicitud>', methods=['PUT'])
@csrf.exempt   # si usás CSRF y tu front es AJAX, esto evita problemas de token
def anular_solicitud(id_solicitud):
    """
    Marca la solicitud de compra como ANULADA.
    """
    try:
        dao = SolicitudCompraDao()
        exito = dao.anular(id_solicitud)
        if exito:
            return jsonify({'success': True, 'message': 'Solicitud anulada correctamente'}), 200
        else:
            return jsonify({'success': False, 'error': 'No se pudo anular la solicitud'}), 400
    except Exception as e:
        app.logger.error(f"Error al anular solicitud: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500
