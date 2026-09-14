from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.marca.MarcaDao import MarcaDao
from app.utilidades.validaciones import validar_texto, error_response, success_response
from app import csrf

marcaapi = Blueprint('marcaapi', __name__)

@marcaapi.route('/marcas', methods=['GET'])
def getMarcas():
    marcao = MarcaDao()
    try:
        marcas = marcao.getMarcas()
        return success_response(data=marcas)
    except Exception as e:
        app.logger.error(f"Error al obtener todas las marcas: {str(e)}")
        return error_response("Ocurrió un error interno al obtener las marcas.", 500)

@marcaapi.route('/marcas/<int:marca_id>', methods=['GET'])
def getMarca(marca_id):
    marcao = MarcaDao()
    try:
        marca = marcao.getMarcaById(marca_id)
        if marca:
            return success_response(data=marca)
        return error_response("No se encontró la marca con el ID proporcionado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener marca: {str(e)}")
        return error_response("Ocurrió un error interno al obtener la marca.", 500)

@marcaapi.route('/marcas', methods=['POST'])
@csrf.exempt
def addMarca():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=50)
    if not ok:
        return error_response(msg, 400)

    marcao = MarcaDao()
    try:
        marca_id = marcao.guardarMarca(descripcion.upper())
        if marca_id:
            return jsonify({
                'success': True,
                'data': {'id': marca_id, 'descripcion': descripcion.upper()},
                'error': None
            }), 201
        return error_response("No se pudo guardar la marca.", 500)
    except Exception as e:
        app.logger.error(f"Error al agregar marca: {str(e)}")
        return error_response("Error interno al guardar la marca.", 500)

@marcaapi.route('/marcas/<int:marca_id>', methods=['PUT'])
@csrf.exempt
def updateMarca(marca_id):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, descripcion = validar_texto(data.get('descripcion'), "Descripción", min_len=2, max_len=50)
    if not ok:
        return error_response(msg, 400)

    marcao = MarcaDao()
    try:
        if marcao.updateMarca(marca_id, descripcion.upper()):
            return success_response(data={'id': marca_id, 'descripcion': descripcion.upper()})
        return error_response("No se encontró la marca o no se pudo actualizar.", 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar marca: {str(e)}")
        return error_response("Error interno al actualizar la marca.", 500)

@marcaapi.route('/marcas/<int:marca_id>', methods=['DELETE'])
@csrf.exempt
def deleteMarca(marca_id):
    marcao = MarcaDao()
    try:
        if marcao.deleteMarca(marca_id):
            return success_response(mensaje=f"Marca {marca_id} eliminada correctamente.")
        return error_response("No se encontró la marca o está asociada a productos/registros existentes.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar marca: {str(e)}")
        return error_response("Error interno al eliminar la marca.", 500)
