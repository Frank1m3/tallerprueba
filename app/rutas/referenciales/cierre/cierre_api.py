from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.cierre.CierreDao import CierreDao
from app.dao.referenciales.apertura.AperturaDao import AperturaDao

cierreapi = Blueprint('cierreapi', __name__)


# ================================
# GET todos los cierres
# ================================
@cierreapi.route('/cierres', methods=['GET'])
def getCierres():
    dao = CierreDao()
    try:
        return jsonify({'success': True, 'data': dao.getCierres(), 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener cierres: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET cierre por ID
# ================================
@cierreapi.route('/cierres/<int:id_cierre>', methods=['GET'])
def getCierre(id_cierre):
    dao = CierreDao()
    try:
        cierre = dao.getCierreById(id_cierre)
        if cierre:
            return jsonify({'success': True, 'data': cierre, 'error': None}), 200
        return jsonify({'success': False, 'error': 'Cierre no encontrado.'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener cierre: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# GET total de ventas de una apertura (para el modal Nuevo Cierre)
# GET /api/v1/cierres/total-ventas/<id_apertura>
# ================================
@cierreapi.route('/cierres/total-ventas/<int:id_apertura>', methods=['GET'])
def getTotalVentas(id_apertura):
    dao  = CierreDao()
    adao = AperturaDao()
    try:
        apertura = adao.getAperturaById(id_apertura)
        if not apertura:
            return jsonify({'success': False, 'error': 'Apertura no encontrada.'}), 404

        totales = dao.getTotalVentasPorApertura(id_apertura)
        return jsonify({
            'success':      True,
            'total_ventas': totales['total_ventas'],
            'cant_ventas':  totales['cant_ventas'],
            'monto_inicial':float(apertura.get('monto_inicial', 0)),
            'nro_turno':    apertura.get('nro_turno'),
            'cajero':       apertura.get('cajero', ''),
            'fiscal':       apertura.get('fiscal', ''),
            'registro':     apertura.get('registro', ''),
        }), 200
    except Exception as e:
        app.logger.error(f"Error al obtener total ventas: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# POST registrar cierre desde apertura activa
# Espera: { id_apertura, observacion? }
# ACTUALIZA la fila que creó el trigger (no inserta otra).
# ================================
@cierreapi.route('/cierres', methods=['POST'])
def addCierre():
    data = request.get_json() or {}
    dao  = CierreDao()
    adao = AperturaDao()

    if not data.get('id_apertura'):
        return jsonify({'success': False, 'error': 'El campo id_apertura es obligatorio.'}), 400

    try:
        apertura = adao.getAperturaById(int(data['id_apertura']))
        if not apertura:
            return jsonify({'success': False, 'error': 'Apertura no encontrada.'}), 404
        if apertura.get('estado') != 'activo':
            return jsonify({'success': False, 'error': 'La apertura no está activa.'}), 400

        res = dao.registrarCierre(
            id_apertura = int(data['id_apertura']),
            observacion = data.get('observacion', '')
        )

        if 'error' in res:
            return jsonify({'success': False, 'error': res['error']}), 400

        return jsonify({
            'success':      True,
            'id_cierre':    res['id_cierre'],
            'monto_final':  res['monto_final'],
            'monto_inicial':res['monto_inicial'],
            'total_ventas': res.get('total_ventas', 0),
            'diferencia':   res['diferencia'],
            'cant_ventas':  res['cant_ventas'],
            'hubo_arqueo':  res.get('hubo_arqueo', False),
            'error':        None
        }), 201

    except Exception as e:
        app.logger.error(f"Error al registrar cierre: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# PATCH cerrar cierre → cierra cierre Y apertura en una transacción
# PATCH /api/v1/cierres/cerrar/<id_cierre>
# ================================
@cierreapi.route('/cierres/cerrar/<int:id_cierre>', methods=['PATCH'])
def cerrarCierre(id_cierre):
    dao = CierreDao()
    try:
        if dao.cerrarCierre(id_cierre):
            return jsonify({'success': True, 'mensaje': f'Cierre {id_cierre} cerrado. Turno finalizado.', 'error': None}), 200
        return jsonify({'success': False, 'error': 'No se pudo cerrar. Verificá que el cierre exista y esté en estado abierto.'}), 404
    except Exception as e:
        app.logger.error(f"Error al cerrar cierre: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500