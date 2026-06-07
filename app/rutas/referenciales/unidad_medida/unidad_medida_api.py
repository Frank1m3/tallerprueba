from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.unidad_medida.UnidadMedidaDao import UnidadMedidaDao
from app import csrf

unidad_medida_api = Blueprint('unidad_medida_api', __name__)

def _validar(data):
    if not data.get('descripcion') or not str(data['descripcion']).strip():
        return "La descripción es obligatoria."
    return None

@unidad_medida_api.route('/unidad_medida', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=UnidadMedidaDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener unidades: {e}")
        return jsonify(success=False, error="Error interno."), 500

@unidad_medida_api.route('/unidad_medida/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = UnidadMedidaDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener unidad: {e}")
        return jsonify(success=False, error="Error interno."), 500

@unidad_medida_api.route('/unidad_medida', methods=['POST'])
@csrf.exempt
def add():
    data = request.get_json() or {}
    err = _validar(data)
    if err: return jsonify(success=False, error=err), 400
    try:
        idr = UnidadMedidaDao().guardar(
            (data.get('codigo') or '').strip(),
            data['descripcion'].strip(),
            (data.get('tipo') or '').strip())
        return (jsonify(success=True, data={"id": idr}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar unidad: {e}")
        return jsonify(success=False, error="Error interno."), 500

@unidad_medida_api.route('/unidad_medida/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    data = request.get_json() or {}
    err = _validar(data)
    if err: return jsonify(success=False, error=err), 400
    try:
        ok = UnidadMedidaDao().update(id,
            (data.get('codigo') or '').strip(),
            data['descripcion'].strip(),
            (data.get('tipo') or '').strip())
        return (jsonify(success=True, data=None, error=None), 200) if ok else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar unidad: {e}")
        return jsonify(success=False, error="Error interno."), 500

@unidad_medida_api.route('/unidad_medida/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminada.", error=None), 200) if UnidadMedidaDao().delete(id) else (jsonify(success=False, error="No encontrada."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar unidad: {e}")
        return jsonify(success=False, error="Error interno."), 500
