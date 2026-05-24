from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.apertura.AperturaDao import AperturaDao
from datetime import datetime

aperapi = Blueprint('aperapi', __name__)


# ================================
# GET todas las aperturas
# ================================
@aperapi.route('/aperturas', methods=['GET'])
def getAperturas():
    dao = AperturaDao()
    try:
        aperturas, ultimo_turno = dao.getAperturas()
        siguiente_turno = (ultimo_turno + 1) if ultimo_turno is not None else 1
        return jsonify({
            'success': True,
            'data': aperturas,
            'siguiente_turno': siguiente_turno,
            'error': None
        }), 200
    except Exception as e:
        app.logger.error(f"Error al obtener aperturas: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET apertura por ID
# ================================
@aperapi.route('/aperturas/<int:id_apertura>', methods=['GET'])
def getApertura(id_apertura):
    dao = AperturaDao()
    try:
        apertura = dao.getAperturaById(id_apertura)
        if apertura:
            return jsonify({'success': True, 'data': apertura, 'error': None}), 200
        return jsonify({'success': False, 'error': 'No encontrado.'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener apertura: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# NUEVO: GET validar fiscal por fun_id (clave ingresada)
# GET /api/v1/aperturas/fiscal/<fun_id>
# ================================
@aperapi.route('/aperturas/fiscal/<int:fun_id>', methods=['GET'])
def getFiscal(fun_id):
    dao = AperturaDao()
    try:
        fiscal = dao.getFiscalByClave(fun_id)
        if fiscal:
            return jsonify({'success': True, 'data': fiscal}), 200
        return jsonify({'success': False, 'error': 'No se encontró un fiscal activo con esa clave.'}), 404
    except Exception as e:
        app.logger.error(f"Error al validar fiscal: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# NUEVO: GET buscar cajeros por nombre/CI
# GET /api/v1/aperturas/cajeros/buscar?q=pedro
# ================================
@aperapi.route('/aperturas/cajeros/buscar', methods=['GET'])
def buscarCajeros():
    termino = request.args.get('q', '').strip()
    if len(termino) < 2:
        return jsonify({'success': True, 'data': []}), 200
    dao = AperturaDao()
    try:
        cajeros = dao.buscarCajeros(termino)
        return jsonify({'success': True, 'data': cajeros}), 200
    except Exception as e:
        app.logger.error(f"Error al buscar cajeros: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# POST crear apertura
# ================================
@aperapi.route('/aperturas', methods=['POST'])
def addApertura():
    data = request.get_json()
    dao = AperturaDao()

    for campo in ['clave_fiscal', 'cajero', 'monto_inicial']:
        if campo not in data or str(data[campo]).strip() == '':
            return jsonify({'success': False, 'error': f'El campo {campo} es obligatorio.'}), 400

    try:
        result = dao.guardarApertura(
            int(data['clave_fiscal']),
            int(data['cajero']),
            data['monto_inicial']
        )
        if result is None:
            return jsonify({
                'success': False,
                'error': 'No se pudo realizar la apertura. Verifique que el fiscal y cajero sean válidos y distintos.'
            }), 400

        apertura = dao.getAperturaById(result['id_apertura'])
        return jsonify({
            'success': True,
            'data': {
                'id_apertura':  result['id_apertura'],
                'nro_turno':    apertura.get('nro_turno') if apertura else None,
                'registro':     apertura.get('registro')  if apertura else None,
                'monto_inicial':data['monto_inicial']
            },
            'error': None
        }), 201

    except Exception as e:
        app.logger.error(f"Error al realizar apertura: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# PATCH anular apertura
# ================================
@aperapi.route('/aperturas/anular/<int:id_apertura>', methods=['PATCH'])
def anularApertura(id_apertura):
    dao = AperturaDao()
    try:
        if dao.anularApertura(id_apertura):
            return jsonify({'success': True, 'mensaje': f'Apertura {id_apertura} anulada.', 'error': None}), 200
        return jsonify({'success': False, 'error': 'No se pudo anular o no se encontró.'}), 404
    except Exception as e:
        app.logger.error(f"Error al anular apertura: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500