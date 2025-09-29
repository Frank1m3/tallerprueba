from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.estado_civil.EstadoCivilDao import EstadoCivilDao

estadocivilapi = Blueprint('estadocivilapi', __name__)

# Estados civiles permitidos
ESTADOS_VALIDOS = ['soltero', 'casado', 'divorciado', 'viudo', 'concubino']

# Trae todos los estados civiles
@estadocivilapi.route('/estadosciviles', methods=['GET'])
def getEstadosCiviles():
    estadocivil_dao = EstadoCivilDao()

    try:
        estados_civiles = estadocivil_dao.getEstadosCiviles()
        return jsonify({
            'success': True,
            'data': estados_civiles,
            'error': None
        }), 200
    except Exception as e:
        app.logger.error(f"Error al obtener todos los estados civiles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Trae un estado civil por ID
@estadocivilapi.route('/estadosciviles/<int:estado_civil_id>', methods=['GET'])
def getEstadoCivil(estado_civil_id):
    estadocivil_dao = EstadoCivilDao()

    try:
        estado_civil = estadocivil_dao.getEstadoCivilById(estado_civil_id)

        if estado_civil:
            return jsonify({
                'success': True,
                'data': estado_civil,
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el estado civil con el ID proporcionado.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al obtener estado civil: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Agrega un nuevo estado civil
@estadocivilapi.route('/estadosciviles', methods=['POST'])
def addEstadoCivil():
    data = request.get_json()
    estadocivil_dao = EstadoCivilDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    if 'descripcion' not in data or not data['descripcion'].strip():
        return jsonify({
            'success': False,
            'error': 'El campo "descripcion" es obligatorio y no puede estar vacío.'
        }), 400

    descripcion = data['descripcion'].lower()
    if descripcion not in ESTADOS_VALIDOS:
        return jsonify({
            'success': False,
            'error': 'El estado debe ser uno de los siguientes: Soltero, Casado, Divorciado, Viudo, Concubino.'
        }), 400

    try:
        descripcion = descripcion.upper()
        estado_civil_id = estadocivil_dao.guardarEstadoCivil(descripcion)
        if estado_civil_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': estado_civil_id, 'descripcion': descripcion},
                'error': None
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo guardar el estado civil. Consulte con el administrador.'
            }), 500
    except Exception as e:
        app.logger.error(f"Error al agregar estado civil: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Actualiza un estado civil existente
@estadocivilapi.route('/estadosciviles/<int:estado_civil_id>', methods=['PUT'])
def updateEstadoCivil(estado_civil_id):
    data = request.get_json()
    estadocivil_dao = EstadoCivilDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    if 'descripcion' not in data or not data['descripcion'].strip():
        return jsonify({
            'success': False,
            'error': 'El campo "descripcion" es obligatorio y no puede estar vacío.'
        }), 400

    descripcion = data['descripcion'].lower()
    if descripcion not in ESTADOS_VALIDOS:
        return jsonify({
            'success': False,
            'error': 'El estado debe ser uno de los siguientes: Soltero, Casado, Divorciado, Viudo, Concubino.'
        }), 400

    try:
        descripcion = descripcion.upper()
        if estadocivil_dao.updateEstadoCivil(estado_civil_id, descripcion):
            return jsonify({
                'success': True,
                'data': {'id': estado_civil_id, 'descripcion': descripcion},
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el estado civil con el ID proporcionado o no se pudo actualizar.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar estado civil: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Elimina un estado civil
@estadocivilapi.route('/estadosciviles/<int:estado_civil_id>', methods=['DELETE'])
def deleteEstadoCivil(estado_civil_id):
    estadocivil_dao = EstadoCivilDao()

    try:
        if estadocivil_dao.deleteEstadoCivil(estado_civil_id):
            return jsonify({
                'success': True,
                'mensaje': f'Estado civil con ID {estado_civil_id} eliminado correctamente.',
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el estado civil con el ID proporcionado o no se pudo eliminar.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar estado civil: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500
