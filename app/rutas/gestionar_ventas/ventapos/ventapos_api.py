from flask import Blueprint, request, jsonify, current_app as app
from app.dao.gestionar_ventas.ventapos.VentaDao import VentaDao

ventaapi = Blueprint('ventaapi', __name__)


# ================================
# Buscar producto
# GET /api/v1/ventas/productos/buscar?q=pan
# ================================
@ventaapi.route('/ventas/productos/buscar', methods=['GET'])
def buscarProducto():
    termino = request.args.get('q', '').strip()
    if not termino:
        return jsonify({'success': True, 'data': []}), 200
    dao = VentaDao()
    try:
        productos = dao.buscarProducto(termino)
        return jsonify({'success': True, 'data': productos}), 200
    except Exception as e:
        app.logger.error(f"Error buscar producto: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Buscar cliente
# GET /api/v1/ventas/clientes/buscar?q=franco
# ================================
@ventaapi.route('/ventas/clientes/buscar', methods=['GET'])
def buscarCliente():
    termino = request.args.get('q', '').strip()
    if len(termino) < 2:
        return jsonify({'success': True, 'data': []}), 200
    dao = VentaDao()
    try:
        clientes = dao.buscarCliente(termino)
        return jsonify({'success': True, 'data': clientes}), 200
    except Exception as e:
        app.logger.error(f"Error buscar cliente: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Siguiente código de venta
# GET /api/v1/ventas/siguiente-codigo
# ================================
@ventaapi.route('/ventas/siguiente-codigo', methods=['GET'])
def siguienteCodigo():
    dao = VentaDao()
    try:
        codigo = dao.getSiguienteCodigoVenta()
        return jsonify({'success': True, 'codigo': codigo}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Formas de pago
# GET /api/v1/ventas/formas-pago
# ================================
@ventaapi.route('/ventas/formas-pago', methods=['GET'])
def getFormasPago():
    dao = VentaDao()
    try:
        formas = dao.getFormasPago()
        return jsonify({'success': True, 'data': formas}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Entidades emisoras
# GET /api/v1/ventas/entidades-emisoras
# ================================
@ventaapi.route('/ventas/entidades-emisoras', methods=['GET'])
def getEntidadesEmisoras():
    dao = VentaDao()
    try:
        data = dao.getEntidadesEmisoras()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        app.logger.error(f"Error entidades emisoras: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Entidades adheridas
# GET /api/v1/ventas/entidades-adheridas
# ================================
@ventaapi.route('/ventas/entidades-adheridas', methods=['GET'])
def getEntidadesAdheridas():
    dao = VentaDao()
    try:
        data = dao.getEntidadesAdheridas()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        app.logger.error(f"Error entidades adheridas: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Registrar venta — falla si no hay apertura activa
# POST /api/v1/ventas
# ================================
@ventaapi.route('/ventas', methods=['POST'])
def registrarVenta():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Sin datos.'}), 400
    if not data.get('detalle') or len(data['detalle']) == 0:
        return jsonify({'success': False, 'error': 'El carrito está vacío.'}), 400
    if not data.get('pagos') or len(data['pagos']) == 0:
        return jsonify({'success': False, 'error': 'Debe registrar al menos un pago.'}), 400

    total_pagado = sum(float(p.get('monto', 0)) for p in data['pagos'])
    total_venta  = float(data.get('total_venta', 0))
    if total_pagado < total_venta:
        return jsonify({'success': False, 'error': 'Monto pagado insuficiente.'}), 400

    dao = VentaDao()
    try:
        codigo_venta = dao.getSiguienteCodigoVenta()
        datos = {
            'fun_id':       data.get('fun_id', 1),
            'id_sucursal':  data.get('id_sucursal', 1),
            'id_caja':      data.get('id_caja', 1),
            'codigo_venta': codigo_venta,
            'id_cliente':   data.get('id_cliente'),
            'total_venta':  total_venta,
            'detalle':      data['detalle'],
            'pagos':        data['pagos']
        }
        resultado = dao.registrarVenta(datos)

        # Sin apertura activa — el DAO devuelve dict con error
        if isinstance(resultado, dict) and 'error' in resultado:
            return jsonify({'success': False, 'error': resultado['error']}), 400

        if resultado:
            return jsonify({'success': True, 'id_venta_cab': resultado, 'codigo_venta': codigo_venta}), 201

        return jsonify({'success': False, 'error': 'No se pudo registrar la venta.'}), 500

    except Exception as e:
        app.logger.error(f"Error registrar venta: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Obtener venta por ID
# GET /api/v1/ventas/<id>
# ================================
@ventaapi.route('/ventas/<int:id_venta>', methods=['GET'])
def getVenta(id_venta):
    dao = VentaDao()
    try:
        venta = dao.getVentaById(id_venta)
        if venta:
            return jsonify({'success': True, 'data': venta}), 200
        return jsonify({'success': False, 'error': 'Venta no encontrada.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500


# ================================
# Listar ventas
# GET /api/v1/ventas
# ================================
@ventaapi.route('/ventas', methods=['GET'])
def getVentas():
    dao = VentaDao()
    try:
        ventas = dao.getVentas()
        return jsonify({'success': True, 'data': ventas}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'Error interno.'}), 500
    

@ventaapi.route('/ventas/clientes/crear_rapido', methods=['POST'])
def crearClienteRapido():
    data = request.get_json() or {}
    if not data.get('cedula') or not data.get('nombre_completo'):
        return jsonify({'success': False, 'error': 'Cédula y nombre son obligatorios.'}), 400
    dao = VentaDao()
    try:
        cliente = dao.crearClienteRapido(data)   # debe devolver el dict del cliente creado
        if cliente:
            return jsonify({'success': True, 'data': cliente}), 201
        return jsonify({'success': False, 'error': 'No se pudo registrar.'}), 500
    except Exception as e:
        app.logger.error(f"Error crear cliente: {e}")
        return jsonify({'success': False, 'error': 'Error interno.'}), 500