# ---------------------- Blueprint API ----------------------
from datetime import date
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_orden_compras.orden_de_compras_dao import OrdenDeComprasDao
from app.dao.gestionar_compras.registrar_orden_compras.dto.orden_de_compras_dto import OrdenDeComprasDto
from app.dao.gestionar_compras.registrar_orden_compras.dto.orden_de_compra_detalle_dto import OrdenDeCompraDetalleDto
from app import csrf

ocapi = Blueprint('ocapi', __name__)


# =================================
# Productos (items) para el combo
# =================================
@ocapi.route('/productos', methods=['GET'])
def get_productos():
    try:
        dao = OrdenDeComprasDao()
        productos = dao.obtener_productos()
        data = [{
            'id_item': p['id_item'],
            'item_code': p['item_code'],
            'producto': p['nombre'],
            'id_proveedor': p['id_proveedor'],
            'proveedor': p['proveedor_nombre'],
            'precio': p['precio_unitario'],
            'stock_actual': p['stock']
        } for p in productos]
        return jsonify(success=True, data=data)
    except Exception as e:
        app.logger.error(f"Error al obtener productos OC: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


# =================================
# Cargar presupuesto por código (prellenar OC)
# =================================
@ocapi.route('/presupuesto/<string:cod_presupuesto>', methods=['GET'])
def get_presupuesto(cod_presupuesto):
    try:
        dao = OrdenDeComprasDao()
        presu = dao.obtener_presupuesto_por_cod(cod_presupuesto)
        if not presu:
            return jsonify(success=False, error='Presupuesto no encontrado'), 404
        return jsonify(success=True, data=presu)
    except Exception as e:
        app.logger.error(f"Error al obtener presupuesto {cod_presupuesto}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


# =================================
# Crear nueva OC
# =================================
@ocapi.route('/ordenes', methods=['POST'])
@csrf.exempt
def crear_orden():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error='Datos incompletos'), 400

        detalle_raw = data.get('detalle_orden', [])
        if not detalle_raw:
            return jsonify(success=False, error='Debe agregar al menos un producto'), 400

        detalle_objs = []
        for d in detalle_raw:
            if not d.get('id_item'):
                return jsonify(success=False, error='Falta id_item en uno de los productos'), 400
            detalle_objs.append(OrdenDeCompraDetalleDto(
                id_item=d.get('id_item'),
                cantidad=d.get('cantidad'),
                precio_unitario=d.get('precio_unitario')
            ))

        id_proveedor = data.get('id_proveedor') or detalle_raw[0].get('id_proveedor')
        if not id_proveedor:
            return jsonify(success=False, error='El proveedor es obligatorio'), 400
        if not data.get('id_deposito'):
            return jsonify(success=False, error='El depósito destino es obligatorio'), 400

        dto = OrdenDeComprasDto(
            id_pre_compra_cab=data.get('id_pre_compra_cab'),
            id_sucursal=data.get('id_sucursal'),
            id_deposito=data.get('id_deposito'),
            fun_id=data.get('fun_id'),
            fecha_emision=data.get('fecha_emision') or date.today().strftime("%Y-%m-%d"),
            id_proveedor=id_proveedor,
            estado=data.get('estado', 'EMITIDA'),
            detalle_orden=detalle_objs
        )

        dao = OrdenDeComprasDao()
        id_cab = dao.agregar(dto)
        if id_cab:
            orden = dao.obtener_orden_por_id(id_cab)
            return jsonify(success=True, id_orden_compra_cab=id_cab,
                           nro_orden=orden.get('nro_orden') if orden else None, error=None)
        return jsonify(success=False, error='No se pudo registrar la orden')
    except Exception as e:
        app.logger.error(f"Error al crear orden: {str(e)}")
        return jsonify(success=False, error=f'Ocurrió un error interno: {str(e)}'), 500


# =================================
# Listado de OC
# =================================
@ocapi.route('/ordenes', methods=['GET'])
def get_ordenes():
    try:
        dao = OrdenDeComprasDao()
        return jsonify(success=True, data=dao.obtener_ordenes())
    except Exception as e:
        app.logger.error(f"Error al obtener órdenes: {str(e)}")
        return jsonify(success=False, data=[], error=str(e))


# =================================
# OC por ID (con detalle)
# =================================
@ocapi.route('/ordenes/<int:id_orden>', methods=['GET'])
def get_orden_por_id(id_orden):
    try:
        dao = OrdenDeComprasDao()
        orden = dao.obtener_orden_por_id(id_orden)
        if not orden:
            return jsonify(success=False, error='Orden no encontrada'), 404
        return jsonify(success=True, data=orden)
    except Exception as e:
        app.logger.error(f"Error al obtener orden ID {id_orden}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


# =================================
# Anular OC
# =================================
@ocapi.route('/ordenes/<int:id_orden>', methods=['DELETE'])
@csrf.exempt
def anular_orden(id_orden):
    try:
        dao = OrdenDeComprasDao()
        if dao.anular(id_orden):
            return jsonify(success=True)
        return jsonify(success=False, error='No se pudo anular la orden')
    except Exception as e:
        app.logger.error(f"Error al anular orden ID {id_orden}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno')
