from flask import Blueprint, request, jsonify, current_app as app
from app.dao.gestionar_ventas.arqueo.ArqueoDao import ArqueoDao

# Registrar este blueprint con prefijo '/api/v1'
arqueoapi = Blueprint('arqueoapi', __name__)


# ================================
# GET lista de arqueos
# GET /api/v1/arqueo
# ================================
@arqueoapi.route('/arqueo', methods=['GET'])
def getArqueos():
    dao = ArqueoDao()
    try:
        return jsonify({'success': True, 'data': dao.getArqueos(), 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener arqueos: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET aperturas activas (para el selector)
# GET /api/v1/arqueo/aperturas-activas
# ================================
@arqueoapi.route('/arqueo/aperturas-activas', methods=['GET'])
def getAperturasActivas():
    dao = ArqueoDao()
    try:
        return jsonify({'success': True, 'data': dao.getAperturasActivas(), 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener aperturas activas: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET datos + totales por forma de una apertura
# GET /api/v1/arqueo/apertura/<id_apertura>
#   → { success, data: {apertura}, totales: [{id_forma, total}] }
# ================================
@arqueoapi.route('/arqueo/apertura/<int:id_apertura>', methods=['GET'])
def getAperturaArqueo(id_apertura):
    dao = ArqueoDao()
    try:
        ap = dao.getAperturaById(id_apertura)
        if not ap:
            return jsonify({'success': False, 'error': 'Apertura no encontrada.'}), 404
        totales = dao.getResumenVentasPorApertura(id_apertura)
        return jsonify({'success': True, 'data': ap, 'totales': totales, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener apertura para arqueo: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET detalle de un arqueo
# GET /api/v1/arqueo/<id_arqueo>
# ================================
@arqueoapi.route('/arqueo/<int:id_arqueo>', methods=['GET'])
def getArqueo(id_arqueo):
    dao = ArqueoDao()
    try:
        arq = dao.getArqueoById(id_arqueo)
        if arq:
            return jsonify({'success': True, 'data': arq, 'error': None}), 200
        return jsonify({'success': False, 'error': 'Arqueo no encontrado.'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener arqueo: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# POST guardar arqueo (NO cierra el turno)
# POST /api/v1/arqueo
# ================================
@arqueoapi.route('/arqueo', methods=['POST'])
def addArqueo():
    data = request.get_json() or {}
    if not data.get('id_apertura'):
        return jsonify({'success': False, 'error': 'Falta id_apertura.'}), 400

    dao = ArqueoDao()
    try:
        res = dao.guardarArqueo(data)
        if 'error' in res:
            return jsonify({'success': False, 'error': res['error']}), 400
        return jsonify({
            'success': True,
            'id_arqueo': res['id_arqueo'],
            'mensaje': 'Arqueo registrado. El turno sigue abierto.',
            'error': None
        }), 201
    except Exception as e:
        app.logger.error(f"Error al guardar arqueo: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500