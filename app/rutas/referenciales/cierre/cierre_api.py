from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.cierre.CierreDao import CierreDao

cierreapi = Blueprint('cierreapi', __name__)

# Obtener todos los cierres
@cierreapi.route('/cierres', methods=['GET'])
def getCierres():
    dao = CierreDao()
    try:
        cierres = dao.getCierres()
        return jsonify({
            'success': True,
            'data': cierres,
            'error': None
        }), 200
    except Exception as e:
        app.logger.error(f"Error al obtener cierres: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno al listar los cierres.'
        }), 500

# Obtener cierre por ID
@cierreapi.route('/cierres/<int:id_cierre>', methods=['GET'])
def getCierre(id_cierre):
    dao = CierreDao()
    try:
        cierre = dao.getCierreById(id_cierre)
        if cierre:
            return jsonify({
                'success': True,
                'data': cierre,
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el cierre con el ID proporcionado.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al obtener cierre: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno.'
        }), 500

# Guardar un cierre
@cierreapi.route('/cierres', methods=['POST'])
def addCierre():
    data = request.get_json()
    dao = CierreDao()

    campos_requeridos = ['monto_final', 'monto_inicial']

    for campo in campos_requeridos:
        if campo not in data or data[campo] is None:
            return jsonify({
                'success': False,
                'error': f'El campo {campo} es obligatorio.'
            }), 400

    try:
        result = dao.guardarCierre(
            data['monto_final'],
            data['monto_inicial'],
            data.get('diferencia'),
            data.get('observacion')
        )

        if result:
            return jsonify({
                'success': True,
                'data': result,
                'error': None
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo registrar el cierre.'
            }), 400

    except Exception as e:
        app.logger.error(f"Error al guardar cierre: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno.'
        }), 500

# Cerrar cierre (cambiar estado a 'cerrado')
@cierreapi.route('/cierres/cerrar/<int:id_cierre>', methods=['PATCH'])
def cerrarCierre(id_cierre):
    dao = CierreDao()
    try:
        if dao.cerrarCierre(id_cierre):
            return jsonify({
                'success': True,
                'mensaje': f'Cierre con ID {id_cierre} cerrado correctamente.',
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo cerrar el cierre o no se encontró el ID.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al cerrar cierre: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor.'
        }), 500
