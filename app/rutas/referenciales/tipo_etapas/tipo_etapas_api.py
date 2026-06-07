from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.tipo_etapas.TipoEtapasDao import TipoEtapasDao
from app import csrf

tipo_etapas_api = Blueprint('tipo_etapas_api', __name__)

@tipo_etapas_api.route('/tipo_etapas', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=TipoEtapasDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener tipo_etapas: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_etapas_api.route('/tipo_etapas/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = TipoEtapasDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener etapa: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_etapas_api.route('/tipo_etapas', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = TipoEtapasDao().guardar(data['descripcion'].strip(), (data.get('tipo_etapa') or '').strip())
        return (jsonify(success=True, data={"id": idr}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar etapa: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_etapas_api.route('/tipo_etapas/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        ok = TipoEtapasDao().update(id, data['descripcion'].strip(), (data.get('tipo_etapa') or '').strip())
        return (jsonify(success=True, data=None, error=None), 200) if ok else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar etapa: {e}")
        return jsonify(success=False, error="Error interno."), 500

@tipo_etapas_api.route('/tipo_etapas/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminada.", error=None), 200) if TipoEtapasDao().delete(id) else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar etapa: {e}")
        return jsonify(success=False, error="Error interno."), 500
