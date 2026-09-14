from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_factura_compras.FacturaCompraDao import FacturaCompraDao
from app import csrf

facapi = Blueprint('facapi', __name__)


@facapi.route('/recepciones-disponibles', methods=['GET'])
def get_recepciones_disponibles():
    try:
        dao = FacturaCompraDao()
        return jsonify(success=True, data=dao.obtener_recepciones_disponibles())
    except Exception as e:
        app.logger.error(f"Error al obtener recepciones disponibles: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


@facapi.route('/facturas', methods=['GET'])
def get_facturas():
    try:
        dao = FacturaCompraDao()
        return jsonify(success=True, data=dao.listar())
    except Exception as e:
        app.logger.error(f"Error al listar facturas: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


@facapi.route('/facturas', methods=['POST'])
@csrf.exempt
def crear_factura():
    try:
        data = request.get_json() or {}
        if not data.get('nro_factura') or not data.get('fecha_emision') or not data.get('id_recepcion'):
            return jsonify(success=False, error='Faltan datos obligatorios (nro. de factura, fecha, recepción)'), 400
        if not data.get('id_proveedor'):
            return jsonify(success=False, error='Falta el proveedor'), 400

        dao = FacturaCompraDao()
        if dao.insertar(data):
            return jsonify(success=True), 201
        return jsonify(success=False, error='No se pudo registrar la factura (¿esa recepción ya tiene una?)'), 400
    except Exception as e:
        app.logger.error(f"Error al crear factura: {str(e)}")
        return jsonify(success=False, error='Ocurrió un error interno.'), 500


@facapi.route('/facturas/<int:id_factura>/estado', methods=['PUT'])
@csrf.exempt
def cambiar_estado_factura(id_factura):
    try:
        data = request.get_json() or {}
        nuevo = (data.get('estado') or '').upper()
        dao = FacturaCompraDao()
        if nuevo not in dao.ESTADOS_VALIDOS:
            return jsonify(success=False, error=f"Estado inválido. Use uno de: {', '.join(dao.ESTADOS_VALIDOS)}"), 400
        ok, msg = dao.cambiar_estado(id_factura, nuevo)
        if ok:
            return jsonify(success=True), 200
        return jsonify(success=False, error=msg or 'No se pudo actualizar'), 400
    except Exception as e:
        app.logger.error(f"Error al cambiar estado de factura {id_factura}: {str(e)}")
        return jsonify(success=False, error='Error interno'), 500
