from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.ciudad.CiudadDao import CiudadDao
from app.utilidades.validaciones import validar_texto, error_response, success_response

ciuapi = Blueprint('ciuapi', __name__)

@ciuapi.route('/ciudades', methods=['GET'])
def getCiudades():
    ciudao = CiudadDao()
    try:
        ciudades = ciudao.getCiudades()
        return success_response(data=ciudades)
    except Exception as e:
        app.logger.error(f"Error al obtener todas las ciudades: {str(e)}")
        return error_response("Ocurrió un error interno al obtener las ciudades.", 500)

@ciuapi.route('/ciudades/<int:ciudad_id>', methods=['GET'])
def getCiudad(ciudad_id):
    ciudao = CiudadDao()
    try:
        ciudad = ciudao.getCiudadById(ciudad_id)
        if ciudad:
            return success_response(data=ciudad)
        return error_response("No se encontró la ciudad con el ID proporcionado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener ciudad: {str(e)}")
        return error_response("Ocurrió un error interno al obtener la ciudad.", 500)

@ciuapi.route('/ciudades', methods=['POST'])
def addCiudad():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60)
    if not ok:
        return error_response(msg, 400)

    ciudao = CiudadDao()
    try:
        descripcion_upper = descripcion.upper()
        ciudad_id = ciudao.guardarCiudad(descripcion_upper)
        if ciudad_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': ciudad_id, 'descripcion': descripcion_upper},
                'error': None
            }), 201
        return error_response("No se pudo guardar la ciudad.", 500)
    except Exception as e:
        app.logger.error(f"Error al agregar ciudad: {str(e)}")
        return error_response("Ocurrió un error interno al guardar la ciudad.", 500)

@ciuapi.route('/ciudades/<int:ciudad_id>', methods=['PUT'])
def updateCiudad(ciudad_id):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60)
    if not ok:
        return error_response(msg, 400)

    ciudao = CiudadDao()
    try:
        descripcion_upper = descripcion.upper()
        if ciudao.updateCiudad(ciudad_id, descripcion_upper):
            return success_response(data={'id': ciudad_id, 'descripcion': descripcion_upper})
        return error_response("No se encontró la ciudad o no se pudo actualizar.", 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar ciudad: {str(e)}")
        return error_response("Ocurrió un error interno al actualizar la ciudad.", 500)

@ciuapi.route('/ciudades/<int:ciudad_id>', methods=['DELETE'])
def deleteCiudad(ciudad_id):
    ciudao = CiudadDao()
    try:
        if ciudao.deleteCiudad(ciudad_id):
            return success_response(mensaje=f"Ciudad con ID {ciudad_id} eliminada correctamente.")
        return error_response("No se encontró la ciudad o no se pudo eliminar por tener dependencias.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar ciudad: {str(e)}")
        return error_response("Ocurrió un error interno al eliminar la ciudad.", 500)