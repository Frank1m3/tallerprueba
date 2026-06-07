from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.marca_tarjeta.MarcaTarjetaDao import MarcaTarjetaDao
from app import csrf

marca_tarjeta_api = Blueprint('marca_tarjeta_api', __name__)

@marca_tarjeta_api.route('/marca_tarjeta', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=MarcaTarjetaDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener marcas de tarjeta: {e}")
        return jsonify(success=False, error="Error interno."), 500

@marca_tarjeta_api.route('/marca_tarjeta/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = MarcaTarjetaDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener marcas de tarjeta: {e}")
        return jsonify(success=False, error="Error interno."), 500

@marca_tarjeta_api.route('/marca_tarjeta', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = MarcaTarjetaDao().guardar(data['descripcion'].strip())
        return (jsonify(success=True, data={"id": idr, "descripcion": data['descripcion'].strip()}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar marcas de tarjeta: {e}")
        return jsonify(success=False, error="Error interno."), 500

@marca_tarjeta_api.route('/marca_tarjeta/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if MarcaTarjetaDao().update(id, data['descripcion'].strip()) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar marcas de tarjeta: {e}")
        return jsonify(success=False, error="Error interno."), 500

@marca_tarjeta_api.route('/marca_tarjeta/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if MarcaTarjetaDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar marcas de tarjeta: {e}")
        return jsonify(success=False, error="Error interno."), 500
