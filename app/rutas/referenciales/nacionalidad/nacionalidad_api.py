from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.nacionalidad.NacionalidadDao import NacionalidadDao
from app.utilidades.validaciones import validar_texto, error_response, success_response

nacapi = Blueprint('nacapi', __name__)

@nacapi.route('/nacionalidades', methods=['GET'])
def getNacionalidades():
    nacdao = NacionalidadDao()
    try:
        nacionalidades = nacdao.getNacionalidades()
        return success_response(data=nacionalidades)
    except Exception as e:
        app.logger.error(f"Error al obtener todas las Nacionalidades: {str(e)}")
        return error_response("Ocurrió un error interno al obtener las nacionalidades.", 500)

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['GET'])
def getNacionalidad(nacionalidad_id):
    nacdao = NacionalidadDao()
    try:
        nacionalidad = nacdao.getNacionalidadById(nacionalidad_id)
        if nacionalidad:
            return success_response(data=nacionalidad)
        return error_response("No se encontró la nacionalidad con el ID proporcionado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener nacionalidad: {str(e)}")
        return error_response("Ocurrió un error interno al obtener la nacionalidad.", 500)

@nacapi.route('/nacionalidades', methods=['POST'])
def addNacionalidad():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    nacdao = NacionalidadDao()
    try:
        descripcion_upper = descripcion.upper()
        nacionalidad_id = nacdao.guardarNacionalidad(descripcion_upper)
        if nacionalidad_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': nacionalidad_id, 'descripcion': descripcion_upper},
                'error': None
            }), 201
        return error_response("No se pudo guardar la nacionalidad.", 500)
    except Exception as e:
        app.logger.error(f"Error al agregar nacionalidad: {str(e)}")
        return error_response("Ocurrió un error interno al guardar la nacionalidad.", 500)

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['PUT'])
def updateNacionalidad(nacionalidad_id):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    nacdao = NacionalidadDao()
    try:
        descripcion_upper = descripcion.upper()
        if nacdao.updateNacionalidad(nacionalidad_id, descripcion_upper):
            return success_response(data={'id': nacionalidad_id, 'descripcion': descripcion_upper})
        return error_response("No se encontró la nacionalidad o no se pudo actualizar.", 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar nacionalidad: {str(e)}")
        return error_response("Ocurrió un error interno al actualizar la nacionalidad.", 500)

@nacapi.route('/nacionalidades/<int:nacionalidad_id>', methods=['DELETE'])
def deleteNacionalidad(nacionalidad_id):
    nacdao = NacionalidadDao()
    try:
        if nacdao.deleteNacionalidad(nacionalidad_id):
            return success_response(mensaje=f"Nacionalidad con ID {nacionalidad_id} eliminada correctamente.")
        return error_response("No se encontró la nacionalidad o no se pudo eliminar por tener dependencias.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar nacionalidad: {str(e)}")
        return error_response("Ocurrió un error interno al eliminar la nacionalidad.", 500)