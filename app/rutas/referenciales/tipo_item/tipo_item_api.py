from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.tipo_item.TipoItemDao import TipoItemDao
from app import csrf

tipo_item_api = Blueprint('tipo_item_api', __name__)

@tipo_item_api.route('/tipo_item', methods=['GET'])
def getAll():
    dao = TipoItemDao()
    try:
        return jsonify(success=True, data=dao.getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener tipo de item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_item_api.route('/tipo_item/<int:id>', methods=['GET'])
def getById(id):
    dao = TipoItemDao()
    try:
        data = dao.getById(id)
        if data:
            return jsonify(success=True, data=data, error=None), 200
        return jsonify(success=False, error="No encontrado."), 404
    except Exception as e:
        app.logger.error(f"Error al obtener tipo de item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_item_api.route('/tipo_item', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    dao = TipoItemDao()
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        id_inserted = dao.guardar(data['descripcion'].strip())
        if id_inserted:
            return jsonify(success=True, data={"id": id_inserted, "descripcion": data['descripcion'].strip()}, error=None), 201
        return jsonify(success=False, error="No se pudo guardar."), 500
    except Exception as e:
        app.logger.error(f"Error al guardar tipo de item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_item_api.route('/tipo_item/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    dao = TipoItemDao()
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        if dao.update(id, data['descripcion'].strip()):
            return jsonify(success=True, data=None, error=None), 200
        return jsonify(success=False, error="No encontrado o no actualizado."), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar tipo de item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_item_api.route('/tipo_item/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    dao = TipoItemDao()
    try:
        if dao.delete(id):
            return jsonify(success=True, mensaje="Eliminado correctamente.", error=None), 200
        return jsonify(success=False, error="No encontrado o no eliminado."), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar tipo de item: {e}")
        return jsonify(success=False, error="Error interno."), 500
