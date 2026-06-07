from flask import Blueprint, request, jsonify, current_app as app
from app.dao.gestionar_ventas.arqueo.ArqueoDao import ArqueoDao

arqueoapi = Blueprint('arqueoapi', __name__)


# GET /api/v1/arqueo/aperturas-activas
@arqueoapi.route('/arqueo/aperturas-activas', methods=['GET'])
def getAperturasActivas():
    dao = ArqueoDao()
    try:
        data = dao.getAperturasActivas()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# GET /api/v1/arqueo/apertura/<id>
@arqueoapi.route('/arqueo/apertura/<int:id_apertura>', methods=['GET'])
def getApertura(id_apertura):
    dao = ArqueoDao()
    try:
        apertura = dao.getAperturaById(id_apertura)
        if not apertura:
            return jsonify({'success': False, 'error': 'Apertura no encontrada.'}), 404
        # Traer totales del sistema por fecha de la apertura
        totales = dao.getTotalesPorFecha(apertura['fecha_apertura'])
        return jsonify({'success': True, 'data': apertura, 'totales': totales}), 200
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# POST /api/v1/arqueo
@arqueoapi.route('/arqueo', methods=['POST'])
def guardarArqueo():
    data = request.get_json()
    if not data or not data.get('id_apertura'):
        return jsonify({'success': False, 'error': 'Datos incompletos.'}), 400
    dao = ArqueoDao()
    try:
        id_arqueo = dao.guardarArqueo(data)
        if id_arqueo:
            return jsonify({'success': True, 'id_arqueo': id_arqueo}), 201
        return jsonify({'success': False, 'error': 'No se pudo guardar el arqueo.'}), 500
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# GET /api/v1/arqueo
@arqueoapi.route('/arqueo', methods=['GET'])
def getArqueos():
    dao = ArqueoDao()
    try:
        return jsonify({'success': True, 'data': dao.getArqueos()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# GET /api/v1/arqueo/<id>
@arqueoapi.route('/arqueo/<int:id_arqueo>', methods=['GET'])
def getArqueo(id_arqueo):
    dao = ArqueoDao()
    try:
        arqueo = dao.getArqueoById(id_arqueo)
        if arqueo:
            return jsonify({'success': True, 'data': arqueo}), 200
        return jsonify({'success': False, 'error': 'No encontrado.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500