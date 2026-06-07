from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.grupo.GrupoDao import GrupoDao
from app import csrf

grupo_api = Blueprint('grupo_api', __name__)

@grupo_api.route('/grupos', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=GrupoDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener grupos: {e}")
        return jsonify(success=False, error="Error interno."), 500

@grupo_api.route('/grupos/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = GrupoDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener grupo: {e}")
        return jsonify(success=False, error="Error interno."), 500

@grupo_api.route('/grupos', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = GrupoDao().guardar(data['descripcion'].strip())
        return (jsonify(success=True, data={"id": idr, "descripcion": data['descripcion'].strip()}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar grupo: {e}")
        return jsonify(success=False, error="Error interno."), 500

@grupo_api.route('/grupos/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if GrupoDao().update(id, data['descripcion'].strip()) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar grupo: {e}")
        return jsonify(success=False, error="Error interno."), 500

@grupo_api.route('/grupos/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if GrupoDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar grupo: {e}")
        return jsonify(success=False, error="Error interno."), 500
