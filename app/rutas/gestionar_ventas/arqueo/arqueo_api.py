from flask import Blueprint, request, jsonify, current_app as app
from app.dao.gestionar_ventas.arqueo.ArqueoDao import ArqueoDao

arqueoapi = Blueprint('arqueoapi', __name__)


# ================================
# GET resumen para arqueo de una apertura
# GET /api/v1/arqueos/resumen/<id_apertura>
#   → esperado por forma de pago + datos del turno
# ================================
@arqueoapi.route('/arqueos/resumen/<int:id_apertura>', methods=['GET'])
def resumenArqueo(id_apertura):
    dao = ArqueoDao()
    try:
        ap = dao.getAperturaById(id_apertura)
        if not ap:
            return jsonify({'success': False, 'error': 'Apertura no encontrada.'}), 404
        if ap.get('estado') != 'activo':
            return jsonify({'success': False, 'error': 'El turno no está activo.'}), 400

        detalle = dao.getResumenVentasPorApertura(id_apertura)
        total_sistema = sum(d['total'] for d in detalle)
        return jsonify({'success': True, 'data': {
            'detalle':       detalle,
            'monto_inicial': ap['monto_inicial'],
            'nro_turno':     ap['nro_turno'],
            'cajero':        ap['cajero'],
            'fiscal':        ap['fiscal'],
            'total_sistema': total_sistema
        }}), 200
    except Exception as e:
        app.logger.error(f"Error resumen arqueo: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# POST finalizar arqueo y cerrar el turno
# Body: { id_apertura, conteos:[{id_forma, monto_contado}], observacion? }
# ================================
@arqueoapi.route('/arqueos/finalizar', methods=['POST'])
def finalizarArqueo():
    data = request.get_json() or {}
    id_apertura = data.get('id_apertura')
    conteos     = data.get('conteos', [])
    observacion = data.get('observacion', '')

    if not id_apertura:
        return jsonify({'success': False, 'error': 'Falta id_apertura.'}), 400
    if not isinstance(conteos, list) or not conteos:
        return jsonify({'success': False, 'error': 'Faltan los conteos por forma de pago.'}), 400

    dao = ArqueoDao()
    res = dao.finalizarArqueo(int(id_apertura), conteos, observacion)
    if 'error' in res:
        return jsonify({'success': False, 'error': res['error']}), 400
    return jsonify({'success': True, 'data': res}), 200


# ================================
# GET listado de arqueos
# ================================
@arqueoapi.route('/arqueos', methods=['GET'])
def getArqueos():
    dao = ArqueoDao()
    try:
        return jsonify({'success': True, 'data': dao.getArqueos()}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener arqueos: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET arqueo por ID
# ================================
@arqueoapi.route('/arqueos/<int:id_arqueo>', methods=['GET'])
def getArqueo(id_arqueo):
    dao = ArqueoDao()
    try:
        arq = dao.getArqueoById(id_arqueo)
        if arq:
            return jsonify({'success': True, 'data': arq}), 200
        return jsonify({'success': False, 'error': 'Arqueo no encontrado.'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener arqueo: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500