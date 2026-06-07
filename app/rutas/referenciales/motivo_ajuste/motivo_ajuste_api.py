from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.motivo_ajuste.MotivoAjusteDao import MotivoAjusteDao
from app import csrf

motivo_ajuste_api = Blueprint('motivo_ajuste_api', __name__)

@motivo_ajuste_api.route('/motivo_ajuste', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=MotivoAjusteDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener motivos de ajuste: {e}")
        return jsonify(success=False, error="Error interno."), 500

@motivo_ajuste_api.route('/motivo_ajuste/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = MotivoAjusteDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener motivo de ajuste: {e}")
        return jsonify(success=False, error="Error interno."), 500

@motivo_ajuste_api.route('/motivo_ajuste', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = MotivoAjusteDao().guardar(data['descripcion'].strip())
        return (jsonify(success=True, data={"id": idr, "descripcion": data['descripcion'].strip()}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar motivo de ajuste: {e}")
        return jsonify(success=False, error="Error interno."), 500

@motivo_ajuste_api.route('/motivo_ajuste/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if MotivoAjusteDao().update(id, data['descripcion'].strip()) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar motivo de ajuste: {e}")
        return jsonify(success=False, error="Error interno."), 500

@motivo_ajuste_api.route('/motivo_ajuste/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if MotivoAjusteDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar motivo de ajuste: {e}")
        return jsonify(success=False, error="Error interno."), 500
