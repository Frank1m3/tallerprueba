from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.moneda.MonedaDao import MonedaDao
from app import csrf

moneda_api = Blueprint('moneda_api', __name__)

def _validar(data):
    if not data.get('codigo') or not str(data['codigo']).strip():
        return "El código es obligatorio."
    if not data.get('descripcion') or not str(data['descripcion']).strip():
        return "La descripción es obligatoria."
    return None

@moneda_api.route('/monedas', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=MonedaDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener monedas: {e}")
        return jsonify(success=False, error="Error interno."), 500

@moneda_api.route('/monedas/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = MonedaDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener moneda: {e}")
        return jsonify(success=False, error="Error interno."), 500

@moneda_api.route('/monedas', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    err = _validar(data)
    if err: return jsonify(success=False, error=err), 400
    try:
        idr = MonedaDao().guardar(data['codigo'].strip(), data['descripcion'].strip())
        return (jsonify(success=True, data={"id": idr}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar moneda: {e}")
        return jsonify(success=False, error="Error interno."), 500

@moneda_api.route('/monedas/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    err = _validar(data)
    if err: return jsonify(success=False, error=err), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if MonedaDao().update(id, data['codigo'].strip(), data['descripcion'].strip()) else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar moneda: {e}")
        return jsonify(success=False, error="Error interno."), 500

@moneda_api.route('/monedas/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminada.", error=None), 200) if MonedaDao().delete(id) else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar moneda: {e}")
        return jsonify(success=False, error="Error interno."), 500
