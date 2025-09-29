from datetime import date
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_pedido_compras.pedido_de_compras_dao import PedidoDeComprasDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app import csrf

pdcapi = Blueprint('pdcapi', __name__)

# ================================
# Obtener siguiente número de pedido
# ================================
@pdcapi.route('/siguiente-nro-pedido', methods=['GET'])
def siguiente_nro_pedido():
    try:
        dao = PedidoDeComprasDao()
        siguiente = dao.obtener_siguiente_nro_pedido()
        return jsonify(success=True, siguiente_nro=siguiente)
    except Exception as e:
        app.logger.error(f"Error al obtener siguiente nro_pedido: {str(e)}")
        return jsonify(success=False, error=str(e))

# ================================
# Obtener funcionarios activos
# ================================
@pdcapi.route('/funcionarios', methods=['GET'])
def get_funcionarios():
    try:
        dao = FuncionarioDao()
        funcionarios = dao.get_funcionarios()
        return jsonify({'success': True, 'data': funcionarios, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener funcionarios: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener productos con stock_actual y proveedor
# ================================
@pdcapi.route('/productos', methods=['GET'])
def get_productos():
    try:
        dao = PedidoDeComprasDao()
        id_sucursal = request.args.get('id_sucursal', type=int)
        id_deposito = request.args.get('id_deposito', type=int)
        productos = dao.obtener_productos(id_sucursal=id_sucursal, id_deposito=id_deposito)
        return jsonify({'success': True, 'data': productos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener productos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener depósitos de una sucursal
# ================================
@pdcapi.route('/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def get_sucursal_depositos(id_sucursal):
    try:
        dao = SucursalDao()
        depositos = dao.get_sucursal_depositos(id_sucursal)
        return jsonify({'success': True, 'data': depositos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Obtener todos los pedidos
# ================================
@pdcapi.route('/pedidos', methods=['GET'])
def get_pedidos():
    try:
        dao = PedidoDeComprasDao()
        pedidos = dao.obtener_pedidos()
        return jsonify({'success': True, 'data': pedidos})
    except Exception as e:
        app.logger.error(f"Error al obtener pedidos: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)})

# ================================
# Crear nuevo pedido
# ================================
@pdcapi.route('/pedidos', methods=['POST'])
@csrf.exempt
def crear_pedido():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compras_dto import PedidoDeComprasDto
        from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto

        detalle_objs = []
        for d in data.get('detalle_pedido', []):
            detalle_objs.append(PedidoDeCompraDetalleDto(
                item_code=d.get('item_code', ''),
                item_descripcion=d.get('item_descripcion', ''),
                id_proveedor=d.get('id_proveedor'),
                cant_pedido=d.get('cant_pedido', 1),
                costo_unitario=d.get('costo_unitario', 0),
                stock_actual=d.get('stock_actual', 0),
                unidad_med=d.get('unidad_med', None),
                tipo_impuesto=d.get('tipo_impuesto', None)
            ))

        # Construcción del DTO usando id_sucursal e id_deposito
        pedido_dto = PedidoDeComprasDto(
            nro_pedido=data.get('nro_pedido', f'PED-{int(date.today().strftime("%Y%m%d"))}'),
            id_funcionario=data.get('id_funcionario'),
            id_sucursal=data.get('id_sucursal'),   # <--- CORREGIDO
            id_deposito=data.get('id_deposito'),   # <--- CORREGIDO
            id_proveedor=data.get('id_proveedor', None),
            detalle_pedido=detalle_objs
        )

        dao = PedidoDeComprasDao()
        exito = dao.agregar(pedido_dto)
        if exito:
            return jsonify({'success': True, 'data': None, 'error': None}), 201
        else:
            return jsonify({'success': False, 'error': 'No se pudo registrar el pedido'}), 500

    except Exception as e:
        app.logger.error(f"Error al crear pedido: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500
