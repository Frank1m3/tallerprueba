from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.item.ItemDao import ItemDao
from app import csrf

item_api = Blueprint('item_api', __name__)

def _num(v):
    """Convierte a numero o None si viene vacio."""
    if v is None or str(v).strip() == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _int(v):
    if v is None or str(v).strip() == '':
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _parse(data):
    return {
        "item_code": (data.get('item_code') or '').strip(),
        "descripcion": (data.get('descripcion') or '').strip(),
        "unidad_med": _int(data.get('unidad_med')),
        "id_tipo_impuesto": _int(data.get('id_tipo_impuesto')),
        "precio_unitario": _num(data.get('precio_unitario')),
        "id_proveedor": _int(data.get('id_proveedor')),
        "id_tipo_item": _int(data.get('id_tipo_item')),
        "cantidad_minima": _num(data.get('cantidad_minima')),
        "activo": bool(data.get('activo', True)),
    }

def _validar(d):
    if not d['item_code']:
        return "El código del item es obligatorio."
    if not d['descripcion']:
        return "La descripción es obligatoria."
    return None

@item_api.route('/item/combos', methods=['GET'])
def combos():
    try:
        return jsonify(success=True, data=ItemDao().getCombos(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener combos item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@item_api.route('/item', methods=['GET'])
def getAll():
    try:
        return jsonify(success=True, data=ItemDao().getItems(), error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener items: {e}")
        return jsonify(success=False, error="Error interno."), 500

@item_api.route('/item/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = ItemDao().getItemById(id)
        return (jsonify(success=True, data=data, error=None), 200) if data else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al obtener item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@item_api.route('/item', methods=['POST'])
@csrf.exempt
def add():
    d = _parse(request.get_json() or {})
    err = _validar(d)
    if err: return jsonify(success=False, error=err), 400
    try:
        idr = ItemDao().guardar(d)
        return (jsonify(success=True, data={"id": idr}, error=None), 201) if idr else (jsonify(success=False, error="No se pudo guardar."), 500)
    except Exception as e:
        app.logger.error(f"Error al guardar item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@item_api.route('/item/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    d = _parse(request.get_json() or {})
    err = _validar(d)
    if err: return jsonify(success=False, error=err), 400
    try:
        return (jsonify(success=True, data=None, error=None), 200) if ItemDao().update(id, d) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar item: {e}")
        return jsonify(success=False, error="Error interno."), 500

@item_api.route('/item/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        return (jsonify(success=True, mensaje="Eliminado.", error=None), 200) if ItemDao().delete(id) else (jsonify(success=False, error="No encontrado."), 404)
    except Exception as e:
        app.logger.error(f"Error al eliminar item: {e}")
        return jsonify(success=False, error="Error interno."), 500
