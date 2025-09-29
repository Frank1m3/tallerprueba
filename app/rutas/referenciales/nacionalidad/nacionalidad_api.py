from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.nacionalidad.NacionalidadDao import NacionalidadDao

nacapi = Blueprint('nacapi', __name__)

# Trae todas las ciudadess
@nacapi.route('/nacionalidades', methods=['GET'])
def getNacionalidades():
    nacdao = NacionalidadDao()

    try:
        nacionalidades = nacdao.getNacionalidades()

        return jsonify({
            'success': True,
            'data': nacionalidades,
            'error': None
        }), 200

    except Exception as e:
        app.logger.error(f"Error al obtener todas las Nacionalidades: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['GET'])
def getNacionalidad(nacionalidad_id):
    nacdao = NacionalidadDao()

    try:
        nacionalidad = nacdao.getNacionalidadById(nacionalidad_id)

        if nacionalidad:
            return jsonify({
                'success': True,
                'data': nacionalidad,
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró la nacionalidad con el ID proporcionado.'
            }), 404

    except Exception as e:
        app.logger.error(f"Error al obtener nacionalidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

# Agrega una nueva ciudad
@nacapi.route('/nacionalidades', methods=['POST'])
def addNacionalidad():
    data = request.get_json()
    nacdao = NacionalidadDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    campos_requeridos = ['descripcion']

    # Verificar si faltan campos o son vacíos
    for campo in campos_requeridos:
        if campo not in data or data[campo] is None or len(data[campo].strip()) == 0:
            return jsonify({
                            'success': False,
                            'error': f'El campo {campo} es obligatorio y no puede estar vacío.'
                            }), 400

    try:
        descripcion = data['descripcion'].upper()
        nacionalidad_id = nacdao.guardarNacionalidad(descripcion)
        if nacionalidad_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': nacionalidad_id, 'descripcion': descripcion},
                'error': None
            }), 201
        else:
            return jsonify({ 'success': False, 'error': 'No se pudo guardar la nacionalidad. Consulte con el administrador.' }), 500
    except Exception as e:
        app.logger.error(f"Error al agregar nacionalidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['PUT'])
def updateNacionalidad(nacionalidad_id):
    data = request.get_json()
    nacdao = NacionalidadDao()

    # Validar que el JSON no esté vacío y tenga las propiedades necesarias
    campos_requeridos = ['descripcion']

    # Verificar si faltan campos o son vacíos
    for campo in campos_requeridos:
        if campo not in data or data[campo] is None or len(data[campo].strip()) == 0:
            return jsonify({
                            'success': False,
                            'error': f'El campo {campo} es obligatorio y no puede estar vacío.'
                            }), 400
    descripcion = data['descripcion']
    try:
        if nacdao.updateNacionalidad(nacionalidad_id, descripcion.upper()):
            return jsonify({
                'success': True,
                'data': {'id': nacionalidad_id, 'descripcion': descripcion},
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró la nacionalidad con el ID proporcionado o no se pudo actualizar.'
            }), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar nacionalidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['DELETE'])
def deleteNacionalidad(nacionalidad_id):
    nacdao = NacionalidadDao()

    try:
        # Usar el retorno de eliminar nacionalidad para determinar el éxito
        if nacdao.deleteNacionalidad(nacionalidad_id):
            return jsonify({
                'success': True,
                'mensaje': f'Nacionalidad con ID {nacionalidad_id} eliminada correctamente.',
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró la nacionalidad con el ID proporcionado o no se pudo eliminar.'
            }), 404

    except Exception as e:
        app.logger.error(f"Error al eliminar nacionalidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500