from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.entidad_emisora.EntidadEmisoraDao import EntidadEmisoraDao
from app import csrf

entidad_emisora_api = Blueprint('entidad_emisora_api', __name__)

@entidad_emisora_api.route('/entidad_emisora', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=EntidadEmisoraDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener entidades emisoras: {e}")
        return jsonify(success=False, error="Error interno."), 500

@entidad_emisora_api.route('/entidad_emisora/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = EntidadEmisoraDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener entidades emisoras: {e}")
        return jsonify(success=False, error="Error interno."), 500

@entidad_emisora_api.route('/entidad_emisora', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = EntidadEmisoraDao().guardar(data['descripcion'].strip())
        return (jsonify(success=True, data={"id": idr, "descripcion": data['descripcion'].strip()}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar entidades emisoras: {e}")
        return jsonify(success=False, error="Error interno."), 500

@entidad_emisora_api.route('/entidad_emisora/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if EntidadEmisoraDao().update(id, data['descripcion'].strip()) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar entidades emisoras: {e}")
        return jsonify(success=False, error="Error interno."), 500

@entidad_emisora_api.route('/entidad_emisora/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if EntidadEmisoraDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar entidades emisoras: {e}")
        return jsonify(success=False, error="Error interno."), 500
