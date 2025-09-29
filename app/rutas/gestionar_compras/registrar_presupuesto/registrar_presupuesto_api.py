from datetime import date
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_presupuesto.PresupuestoDao import PresupuestoCompraDao
from app.dao.referenciales.proveedor.ProveedorDao import ProveedorDao
from app import csrf

presuapi = Blueprint('presuapi', __name__)

# ================================
# Obtener siguiente código de presupuesto
# ================================
@presuapi.route('/siguiente-codigo', methods=['GET'])
def siguiente_codigo():
    try:
        dao = PresupuestoCompraDao()
        siguiente = dao.obtener_siguiente_codigo()
        return jsonify(success=True, siguiente_codigo=siguiente)
    except Exception as e:
        app.logger.error(f"Error al obtener siguiente código: {str(e)}")
        return jsonify(success=False, error=str(e))

# ================================
# Listar todos los presupuestos (cabecera)
# ================================
@presuapi.route('/presupuestos', methods=['GET'])
def listar_presupuestos():
    try:
        dao = PresupuestoCompraDao()
        presupuestos = dao.listar()
        return jsonify({'success': True, 'data': presupuestos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al listar presupuestos: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)}), 500

# ================================
# Crear nuevo presupuesto
# ================================
@presuapi.route('/presupuestos', methods=['POST'])
@csrf.exempt
def crear_presupuesto():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_dto import PresupuestoCompraDto
        from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_detalle_dto import PresupuestoCompraDetalleDto

        detalles_objs = [
            PresupuestoCompraDetalleDto(
                item_code=d.get('item_code', ''),
                cantidad=d.get('cantidad', 0),
                precio_unitario=d.get('precio_unitario', 0)
            )
            for d in data.get('detalles', [])
        ]

        presupuesto_dto = PresupuestoCompraDto(
            cod_presupuesto=data.get('cod_presupuesto', f'PRE-{int(date.today().strftime("%Y%m%d"))}'),
            fun_id=data.get('fun_id'),
            id_proveedor=data.get('id_proveedor'),
            fecha_emision=data.get('fecha_emision', date.today()),
            fecha_vencimiento=data.get('fecha_vencimiento'),
            condicion_compra=data.get('condicion_compra'),
            estado=data.get('estado', 'PENDIENTE'),
            detalles=detalles_objs
        )

        dao = PresupuestoCompraDao()
        exito = dao.insertar(presupuesto_dto)
        if exito:
            return jsonify({'success': True, 'data': None, 'error': None}), 201
        else:
            return jsonify({'success': False, 'error': 'No se pudo registrar el presupuesto'}), 500

    except Exception as e:
        app.logger.error(f"Error al crear presupuesto: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Listar proveedores
# ================================
@presuapi.route('/proveedores', methods=['GET'])
def listar_proveedores():
    try:
        dao = ProveedorDao()
        proveedores = dao.getProveedores()
        return jsonify({'success': True, 'data': proveedores, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al listar proveedores: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)}), 500

# ================================
# Listar mercaderías (items) con stock
# ================================
@presuapi.route('/mercaderias', methods=['GET'])
def listar_mercaderias():
    try:
        id_sucursal = request.args.get('id_sucursal', type=int)
        dao = PresupuestoCompraDao()
        productos = dao.buscar_mercaderias(filtro='', id_sucursal=id_sucursal)
        return jsonify({'success': True, 'data': productos, 'error': None}), 200
    except Exception as e:
        app.logger.error(f"Error al listar mercaderías: {str(e)}")
        return jsonify({'success': False, 'data': [], 'error': str(e)}), 500

# ================================
# Buscar mercadería por filtro (código, descripción, barras)
# ================================
@presuapi.route('/buscar-mercaderia', methods=['GET'])
def buscar_mercaderia():
    try:
        filtro = request.args.get('filtro', '')
        id_sucursal = request.args.get('id_sucursal', None)
        if id_sucursal:
            id_sucursal = int(id_sucursal)

        dao = PresupuestoCompraDao()
        resultados = dao.buscar_mercaderias(filtro=filtro, id_sucursal=id_sucursal)
        return jsonify(success=True, data=resultados)
    except Exception as e:
        app.logger.error(f"Error al buscar mercaderías: {str(e)}")
        return jsonify(success=False, error=str(e))
