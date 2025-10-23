# ---------------------- Blueprint ----------------------
from datetime import date
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_pedido_compras.pedido_de_compras_dao import PedidoDeComprasDao
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compras_dto import PedidoDeComprasDto
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto
from app import csrf

pdcapi = Blueprint('pdcapi', __name__)

# =================================
# Obtener proveedor de un producto
# =================================
@pdcapi.route('/item-proveedor/<string:id_item>', methods=['GET'])
def get_item_proveedor(id_item):
    try:
        dao = PedidoDeComprasDao()
        producto = dao.obtener_producto_por_id(id_item)
        if not producto:
            return jsonify(success=False, error='Producto no encontrado'), 404

        return jsonify(
            success=True,
            id_proveedor=producto.get('id_proveedor'),
            proveedor=producto.get('proveedor_nombre','')
        )
    except Exception as e:
        app.logger.error(f"Error al obtener proveedor del item {id_item}: {str(e)}")
        return jsonify(success=False, error=f'Ocurrió un error interno: {str(e)}'), 500

# =================================
# Siguiente número de pedido
# =================================
@pdcapi.route('/siguiente-nro-pedido', methods=['GET'])
def siguiente_nro_pedido():
    try:
        dao = PedidoDeComprasDao()
        siguiente = dao.obtener_siguiente_nro_pedido()
        return jsonify(success=True, siguiente_nro=siguiente)
    except Exception as e:
        app.logger.error(f"Error al obtener siguiente nro_pedido: {str(e)}")
        return jsonify(success=False, error=str(e))

# =================================
# Obtener productos
# =================================
@pdcapi.route('/productos', methods=['GET'])
def get_productos():
    try:
        dao = PedidoDeComprasDao()
        id_sucursal = request.args.get('id_sucursal', type=int)
        id_deposito = request.args.get('id_deposito', type=int)
        productos = dao.obtener_productos(id_sucursal=id_sucursal, id_deposito=id_deposito)

        productos_formateados = []
        for p in productos:
            productos_formateados.append({
                'id_item': p.get('item_code'),
                'item_code': p.get('item_code'),
                'codigo': p.get('item_code'),
                'producto': p.get('nombre'),
                'id_proveedor': p.get('id_proveedor'),
                'proveedor': p.get('proveedor_nombre',''),
                'stock_actual': p.get('stock',0),
                'precio': p.get('precio_unitario',0)
            })
        return jsonify(success=True, data=productos_formateados)
    except Exception as e:
        app.logger.error(f"Error al obtener productos: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500

# =================================
# Obtener depósitos por sucursal
# =================================
@pdcapi.route('/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def get_sucursal_depositos(id_sucursal):
    try:
        from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
        dao = SucursalDao()
        depositos = dao.get_sucursal_depositos(id_sucursal)
        return jsonify(success=True, data=depositos)
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500

# =================================
# Crear nuevo pedido
# =================================
@pdcapi.route('/pedidos', methods=['POST'])
@csrf.exempt
def crear_pedido():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error='Datos incompletos'), 400

        detalle_raw = data.get('detalle_pedido', [])
        if not detalle_raw:
            return jsonify(success=False, error='Debe agregar al menos un producto'), 400

        detalle_objs = []
        for d in detalle_raw:
            if not d.get('id_proveedor'):
                return jsonify(success=False, error=f'Falta id_proveedor para {d.get("item_descripcion") or d.get("producto","")}'), 400

            detalle_objs.append(PedidoDeCompraDetalleDto(
                id_item=d.get('item_code'),
                item_code=d.get('item_code'),
                item_descripcion=d.get('item_descripcion') or d.get('producto',''),
                cant_pedido=d.get('cant_pedido'),
                costo_unitario=d.get('costo_unitario'),
                stock_actual=d.get('stock',0),
                unidad_med=d.get('unidad_med', None),
                tipo_impuesto=d.get('tipo_impuesto', None),
                id_proveedor=d.get('id_proveedor')
            ))

        id_proveedor_cab = data.get('id_proveedor') or detalle_raw[0].get('id_proveedor')
        if not id_proveedor_cab:
            return jsonify(success=False, error='El id_proveedor no puede ser None al crear un pedido'), 400

        pedido_dto = PedidoDeComprasDto(
            nro_pedido = data.get('nro_pedido', f'PED-{int(date.today().strftime("%Y%m%d"))}'),
            nro_solicitud = data.get('nro_solicitud'),
            id_funcionario = data.get('id_funcionario'),
            id_sucursal = data.get('id_sucursal'),
            id_deposito = data.get('id_deposito'),
            fecha_pedido = data.get('fecha_pedido'),
            fecha_necesaria = data.get('fecha_necesaria'),
            id_proveedor = id_proveedor_cab,
            detalle_pedido = detalle_objs,
            tipo_factura = data.get('tipo_factura')
        )

        dao = PedidoDeComprasDao()
        exito = dao.agregar(pedido_dto)
        return jsonify(success=exito, error=None if exito else 'No se pudo registrar el pedido')
    except Exception as e:
        app.logger.error(f"Error al crear pedido: {str(e)}")
        return jsonify(success=False, error=f'Ocurrió un error interno: {str(e)}'), 500

# =================================
# Obtener solicitud por nro
# =================================
@pdcapi.route('/solicitud-nro/<string:nro_solicitud>', methods=['GET'])
def get_solicitud_por_nro(nro_solicitud):
    try:
        dao = PedidoDeComprasDao()
        solicitud = dao.obtener_solicitud_por_nro(nro_solicitud)
        if not solicitud:
            return jsonify(success=False, error='Solicitud no encontrada'), 404

        detalle_formateado = []
        for d in solicitud.get('detalle', []):
            detalle_formateado.append({
                'id_item': d.get('item_code'),
                'item_code': d.get('item_code'),
                'codigo': d.get('item_code'),
                'producto': d.get('item_descripcion') or d.get('producto',''),
                'cant_pedido': float(d.get('cant_pedido',0)),
                'precio': float(d.get('costo_unitario',0)),
                'stock_actual': float(d.get('stock',0)),
                'proveedor': d.get('proveedor',''),
                'id_proveedor': d.get('id_proveedor')
            })
        solicitud['detalle'] = detalle_formateado

        return jsonify(success=True, data=solicitud)
    except Exception as e:
        app.logger.error(f"Error al obtener solicitud nro {nro_solicitud}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500

# =================================
# Obtener todos los pedidos
# =================================
@pdcapi.route('/pedidos', methods=['GET'])
def get_pedidos():
    try:
        dao = PedidoDeComprasDao()
        pedidos = dao.obtener_pedidos()
        pedidos_formateados = []
        for p in pedidos:
            pedidos_formateados.append({
                'id_pedido_compra_cab': p['id_pedido_compra_cab'],
                'nro_pedido': p['nro_pedido'],
                'fecha_pedido': p['fecha_pedido'],
                'funcionario': p['funcionario'],
                'sucursal': p['sucursal'],
                'deposito': p['deposito'],
                'id_proveedor': p['id_proveedor'],
                'proveedor_nombre': p['proveedor_nombre'],
                'tipo_factura': p.get('tipo_factura','')
            })
        return jsonify(success=True, data=pedidos_formateados)
    except Exception as e:
        app.logger.error(f"Error al obtener pedidos: {str(e)}")
        return jsonify(success=False, data=[], error=str(e))

# =================================
# Obtener pedido completo por ID (con detalle)
# =================================
@pdcapi.route('/pedidos/<int:id_pedido>', methods=['GET'])
def get_pedido_por_id(id_pedido):
    try:
        dao = PedidoDeComprasDao()
        pedido = dao.obtener_pedido_por_id(id_pedido)
        if not pedido:
            return jsonify(success=False, error='Pedido no encontrado'), 404

        # Formatear detalle
        detalle_formateado = []
        for d in pedido.get('detalle', []):
            detalle_formateado.append({
                'item_code': d.get('item_code'),
                'producto': d.get('item_descripcion'),
                'unidad_med': d.get('unidad_med'),
                'cant_pedido': float(d.get('cant_pedido',0)),
                'costo_unitario': float(d.get('costo_unitario',0)),
                'tipo_impuesto': d.get('tipo_impuesto')
            })
        pedido['detalle'] = detalle_formateado

        return jsonify(success=True, data=pedido)
    except Exception as e:
        app.logger.error(f"Error al obtener pedido ID {id_pedido}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500
# =================================
# Anular un pedido
# =================================
@pdcapi.route('/pedidos/<int:id_pedido>', methods=['DELETE'])
@csrf.exempt  # Si estás usando CSRF
def anular_pedido(id_pedido):
    try:
        dao = PedidoDeComprasDao()
        exito = dao.anular(id_pedido)
        if exito:
            return jsonify(success=True)
        else:
            return jsonify(success=False, error='No se pudo anular el pedido')
    except Exception as e:
        app.logger.error(f"Error al anular pedido ID {id_pedido}: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno')
