from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.sexo.SexoDao import SexoDao

sexoapi = Blueprint('sexoapi', __name__)

# Sexos permitidos
SEXOS_VALIDOS = ['femenino', 'masculino', 'otro']

# Trae todos los sexos
@sexoapi.route('/sexos', methods=['GET'])
def getSexos():
    sexo_dao = SexoDao()

    try:
        sexos = sexo_dao.getSexos()
        return jsonify({
            'success': True,
            'data': sexos,
            'error': None
        }), 200
    except Exception as e:
        app.logger.error(f"Error al obtener todos los sexos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Trae un sexo por ID
@sexoapi.route('/sexos/<int:sexo_id>', methods=['GET'])
def getSexo(sexo_id):
    sexo_dao = SexoDao()

    try:
        sexo = sexo_dao.getSexoById(sexo_id)

        if sexo:
            return jsonify({
                'success': True,
                'data': sexo,
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el sexo con el ID proporcionado.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al obtener sexo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Agrega un nuevo sexo
@sexoapi.route('/sexos', methods=['POST'])
def addSexo():
    data = request.get_json()
    sexo_dao = SexoDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    if 'descripcion' not in data or not data['descripcion'].strip():
        return jsonify({
            'success': False,
            'error': 'El campo "descripcion" es obligatorio y no puede estar vacío.'
        }), 400

    descripcion = data['descripcion'].lower()

    # Validar el sexo
    if descripcion not in SEXOS_VALIDOS:
        return jsonify({
            'success': False,
            'error': 'El sexo debe ser uno de los siguientes: Femenino, Masculino, Otro.'
        }), 400

    try:
        # Convertir a mayúsculas
        descripcion = descripcion.upper()

        sexo_id = sexo_dao.guardarSexo(descripcion)
        if sexo_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': sexo_id, 'descripcion': descripcion},
                'error': None
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo guardar el sexo. Consulte con el administrador.'
            }), 500
    except Exception as e:
        app.logger.error(f"Error al agregar sexo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Actualiza un sexo existente
@sexoapi.route('/sexos/<int:sexo_id>', methods=['PUT'])
def updateSexo(sexo_id):
    data = request.get_json()
    sexo_dao = SexoDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    if 'descripcion' not in data or not data['descripcion'].strip():
        return jsonify({
            'success': False,
            'error': 'El campo "descripcion" es obligatorio y no puede estar vacío.'
        }), 400

    descripcion = data['descripcion'].lower()

    if descripcion not in SEXOS_VALIDOS:
        return jsonify({
            'success': False,
            'error': 'El sexo debe ser uno de los siguientes: Femenino, Masculino, Otro.'
        }), 400

    try:
        descripcion = descripcion.upper()

        if sexo_dao.updateSexo(sexo_id, descripcion):
            return jsonify({
                'success': True,
                'data': {'id': sexo_id, 'descripcion': descripcion},
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el sexo con el ID proporcionado o no se pudo actualizar.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar sexo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Elimina un sexo
@sexoapi.route('/sexos/<int:sexo_id>', methods=['DELETE'])
def deleteSexo(sexo_id):
    sexo_dao = SexoDao()

    try:
        if sexo_dao.deleteSexo(sexo_id):
            return jsonify({
                'success': True,
                'mensaje': f'Sexo con ID {sexo_id} eliminado correctamente.',
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró el sexo con el ID proporcionado o no se pudo eliminar.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar sexo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500
