from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.item.ItemDao import ItemDao
from app.utilidades.validaciones import (
    validar_texto, validar_entero, validar_decimal,
    error_response, success_response
)
from app import csrf

item_api = Blueprint('item_api', __name__)

def _parse_and_validate(raw_data):
    if not raw_data or not isinstance(raw_data, dict):
        return False, "El cuerpo de la petición debe ser un objeto JSON válido.", None

    # Validar código
    ok, msg, item_code = validar_texto(raw_data.get('item_code'), "Código de Item", min_len=1, max_len=50)
    if not ok:
        return False, msg, None

    # Validar descripción
    ok, msg, descripcion = validar_texto(raw_data.get('descripcion'), "Descripción", min_len=2, max_len=150)
    if not ok:
        return False, msg, None

    # Validar precio unitario
    precio_raw = raw_data.get('precio_unitario')
    if precio_raw is not None and precio_raw != '':
        ok, msg, precio_unitario = validar_decimal(precio_raw, "Precio Unitario", min_val=0)
        if not ok:
            return False, msg, None
    else:
        precio_unitario = 0.0

    # Validar cantidad mínima
    cant_min_raw = raw_data.get('cantidad_minima')
    if cant_min_raw is not None and cant_min_raw != '':
        ok, msg, cantidad_minima = validar_decimal(cant_min_raw, "Cantidad Mínima", min_val=0)
        if not ok:
            return False, msg, None
    else:
        cantidad_minima = 0.0

    # Validar claves foráneas
    def _parse_fk(v, nombre):
        if v is None or v == '':
            return True, None
        return validar_entero(v, nombre, min_val=1)

    ok, msg, unidad_med = _parse_fk(raw_data.get('unidad_med'), "Unidad de Medida")
    if not ok: return False, msg, None

    ok, msg, id_tipo_impuesto = _parse_fk(raw_data.get('id_tipo_impuesto'), "Tipo de Impuesto")
    if not ok: return False, msg, None

    ok, msg, id_proveedor = _parse_fk(raw_data.get('id_proveedor'), "Proveedor")
    if not ok: return False, msg, None

    ok, msg, id_tipo_item = _parse_fk(raw_data.get('id_tipo_item'), "Tipo de Item")
    if not ok: return False, msg, None

    return True, "", {
        "item_code": item_code,
        "descripcion": descripcion,
        "unidad_med": unidad_med,
        "id_tipo_impuesto": id_tipo_impuesto,
        "precio_unitario": precio_unitario,
        "id_proveedor": id_proveedor,
        "id_tipo_item": id_tipo_item,
        "cantidad_minima": cantidad_minima,
        "activo": bool(raw_data.get('activo', True)),
    }

@item_api.route('/item/buscar', methods=['GET'])
def buscar():
    """Búsqueda acotada para los buscadores remotos (producto en solicitudes,
    órdenes, pedidos, etc). No devuelve el catálogo completo: requiere texto
    de búsqueda o al menos limita a `limit` resultados (máx 50)."""
    try:
        q = (request.args.get('q') or '').strip()
        id_sucursal = request.args.get('id_sucursal', type=int)
        id_deposito = request.args.get('id_deposito', type=int)
        id_proveedor = request.args.get('id_proveedor', type=int)
        limit = request.args.get('limit', 30, type=int) or 30
        data = ItemDao().buscar(q=q, id_sucursal=id_sucursal, id_deposito=id_deposito,
                                 id_proveedor=id_proveedor, limit=limit)
        return success_response(data=data)
    except Exception as e:
        app.logger.error(f"Error al buscar items: {e}")
        return error_response("Error interno al buscar items.", 500)

@item_api.route('/item/combos', methods=['GET'])
def combos():
    try:
        return success_response(data=ItemDao().getCombos())
    except Exception as e:
        app.logger.error(f"Error al obtener combos item: {e}")
        return error_response("Error interno al obtener combos.", 500)

@item_api.route('/item', methods=['GET'])
def getAll():
    try:
        return success_response(data=ItemDao().getItems())
    except Exception as e:
        app.logger.error(f"Error al obtener items: {e}")
        return error_response("Error interno al obtener items.", 500)

@item_api.route('/item/<int:id>', methods=['GET'])
def getById(id):
    try:
        data = ItemDao().getItemById(id)
        if data:
            return success_response(data=data)
        return error_response("Item no encontrado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener item: {e}")
        return error_response("Error interno al obtener item.", 500)

@item_api.route('/item', methods=['POST'])
@csrf.exempt
def add():
    ok, err, d = _parse_and_validate(request.get_json())
    if not ok:
        return error_response(err, 400)
    try:
        idr = ItemDao().guardar(d)
        if idr:
            return success_response(data={"id": idr}, status_code=201)
        return error_response("No se pudo guardar el item. Verifique los datos foráneos.", 400)
    except Exception as e:
        app.logger.error(f"Error al guardar item: {e}")
        return error_response("Error interno al guardar item.", 500)

@item_api.route('/item/<int:id>', methods=['PUT'])
@csrf.exempt
def update(id):
    ok, err, d = _parse_and_validate(request.get_json())
    if not ok:
        return error_response(err, 400)
    try:
        if ItemDao().update(id, d):
            return success_response(data={"id": id})
        return error_response("Item no encontrado o no se pudo actualizar.", 404)
    except Exception as e:
        app.logger.error(f"Error al actualizar item: {e}")
        return error_response("Error interno al actualizar item.", 500)

@item_api.route('/item/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete(id):
    try:
        if ItemDao().delete(id):
            return success_response(mensaje="Item eliminado correctamente.")
        return error_response("No se puede eliminar el item porque posee movimientos o compras/ventas asociadas.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar item: {e}")
        return error_response("Error interno al eliminar item.", 500)
