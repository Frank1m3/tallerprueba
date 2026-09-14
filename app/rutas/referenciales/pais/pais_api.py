from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.pais.PaisDao import PaisDao
from app.utilidades.validaciones import validar_texto, error_response, success_response

paiapi = Blueprint('paiapi', __name__)

@paiapi.route('/paises', methods=['GET'])
def getPaises():
    paisdao = PaisDao()
    try:
        paises = paisdao.getPaises()
        return success_response(data=paises)
    except Exception as e:
        app.logger.error(f"Error al obtener todos los paises: {str(e)}")
        return error_response("Ocurrió un error interno al obtener los países.", 500)

@paiapi.route('/paises/<int:pais_id>', methods=['GET'])
def getPais(pais_id):
    paisdao = PaisDao()
    try:
        pais = paisdao.getPaisById(pais_id)
        if pais:
            return success_response(data=pais)
        return error_response("No se encontró el país con el ID proporcionado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener pais: {str(e)}")
        return error_response("Ocurrió un error interno al obtener el país.", 500)

@paiapi.route('/paises', methods=['POST'])
def addPais():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    paisdao = PaisDao()
    try:
        descripcion_upper = descripcion.upper()
        pais_id = paisdao.guardarPais(descripcion_upper)
        if pais_id is not None:
            return jsonify({
                'success': True,
                'data': {'id': pais_id, 'descripcion': descripcion_upper},
                'error': None
            }), 201
        return error_response("No se pudo guardar el país.", 500)
    except Exception as e:
        app.logger.error(f"Error al agregar pais: {str(e)}")
        return error_response("Ocurrió un error interno al guardar el país.", 500)

@paiapi.route('/paises/<int:pais_id>', methods=['PUT'])
def updatePais(pais_id):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=60, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    paisdao = PaisDao()
    try:
        descripcion_upper = descripcion.upper()
        if paisdao.updatePais(pais_id, descripcion_upper):
            return success_response(data={'id': pais_id, 'descripcion': descripcion_upper})
        return error_response("No se encontró el país o no se pudo actualizar.", 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar pais: {str(e)}")
        return error_response("Ocurrió un error interno al actualizar el país.", 500)

@paiapi.route('/paises/<int:pais_id>', methods=['DELETE'])
def deletePais(pais_id):
    paisdao = PaisDao()
    try:
        if paisdao.deletePais(pais_id):
            return success_response(mensaje=f"País con ID {pais_id} eliminado correctamente.")
        return error_response("No se encontró el país o no se pudo eliminar por tener dependencias.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar pais: {str(e)}")
        return error_response("Ocurrió un error interno al eliminar el país.", 500)