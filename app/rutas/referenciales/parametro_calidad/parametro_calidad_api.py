from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.parametro_calidad.ParametroCalidadDao import ParametroCalidadDao
from app import csrf

parametro_calidad_api = Blueprint('parametro_calidad_api', __name__)

def _num(v):
    if v is None or str(v).strip() == '': return None
    try: return float(v)
    except (TypeError, ValueError): return None

def _int(v):
    if v is None or str(v).strip() == '': return None
    try: return int(v)
    except (TypeError, ValueError): return None

def _parse(data):
    return {
        "descripcion": (data.get('descripcion') or '').strip(),
        "valor_minimo": _num(data.get('valor_minimo')),
        "valor_maximo": _num(data.get('valor_maximo')),
        "id_tipo_etapa": _int(data.get('id_tipo_etapa')),
        "id_unidad_medida": _int(data.get('id_unidad_medida')),
    }

@parametro_calidad_api.route('/parametro_calidad/combos', methods=['GET'])
def combos():
    try:
        return jsonify(success=True, data=ParametroCalidadDao().getCombos(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener combos parametros: {e}")
        return jsonify(success=False, error="Error interno."), 500

@parametro_calidad_api.route('/parametro_calidad', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=ParametroCalidadDao().getAll(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener parametros: {e}")
        return jsonify(success=False, error="Error interno."), 500

@parametro_calidad_api.route('/parametro_calidad/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = ParametroCalidadDao().getById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener parametro: {e}")
        return jsonify(success=False, error="Error interno."), 500

@parametro_calidad_api.route('/parametro_calidad', methods=['POST'])
@csrf.exempt
def add():
    d = _parse(request.get_json() or {})
    if not d['descripcion']:
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        idr = ParametroCalidadDao().guardar(d)
        return (jsonify(success=True, data={"id": idr}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar parametro: {e}")
        return jsonify(success=False, error="Error interno."), 500

@parametro_calidad_api.route('/parametro_calidad/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    d = _parse(request.get_json() or {})
    if not d['descripcion']:
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if ParametroCalidadDao().update(id, d) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar parametro: {e}")
        return jsonify(success=False, error="Error interno."), 500

@parametro_calidad_api.route('/parametro_calidad/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if ParametroCalidadDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar parametro: {e}")
        return jsonify(success=False, error="Error interno."), 500
