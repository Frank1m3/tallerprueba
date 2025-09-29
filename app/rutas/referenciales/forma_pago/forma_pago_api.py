from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.forma_pago.FormaPagoDao import FormaPagoDao
from app import csrf

forma_pago_api = Blueprint('forma_pago_api', __name__)

@forma_pago_api.route('/formas_pago', methods=['GET'])
def getFormasPago():
    dao = FormaPagoDao()
    try:
        data = dao.getFormasPago()
        return jsonify(success=True, data=data, error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener formas de pago: {e}")
        return jsonify(success=False, error="Error interno."), 500

@forma_pago_api.route('/formas_pago/<int:id>', methods=['GET'])
def getFormaPago(id):
    dao = FormaPagoDao()
    try:
        data = dao.getFormaPagoById(id)
        if data:
            return jsonify(success=True, data=data, error=None), 200
        else:
            return jsonify(success=False, error="No encontrada."), 404
    except Exception as e:
        app.logger.error(f"Error al obtener forma de pago: {e}")
        return jsonify(success=False, error="Error interno."), 500

@forma_pago_api.route('/formas_pago', methods=['POST'])
@csrf.exempt  # Exento para llamadas API, en caso contrario configuras tokens en frontend
def addFormaPago():
    data = request.get_json() or {}
    dao = FormaPagoDao()
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        id_inserted = dao.guardarFormaPago(data['descripcion'].strip())
        if id_inserted:
            return jsonify(success=True, data={"id": id_inserted, "descripcion": data['descripcion'].strip()}, error=None), 201
        else:
            return jsonify(success=False, error="No se pudo guardar."), 500
    except Exception as e:
        app.logger.error(f"Error al guardar forma de pago: {e}")
        return jsonify(success=False, error="Error interno."), 500

@forma_pago_api.route('/formas_pago/<int:id>', methods=['PUT'])
@csrf.exempt
def updateFormaPago(id):
    data = request.get_json() or {}
    dao = FormaPagoDao()
    if not data.get('descripcion') or not data['descripcion'].strip():
        return jsonify(success=False, error="La descripción es obligatoria."), 400
    try:
        updated = dao.updateFormaPago(id, data['descripcion'].strip())
        if updated:
            return jsonify(success=True, data=None, error=None), 200
        else:
            return jsonify(success=False, error="No encontrada o no actualizada."), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar forma de pago: {e}")
        return jsonify(success=False, error="Error interno."), 500

@forma_pago_api.route('/formas_pago/<int:id>', methods=['DELETE'])
@csrf.exempt
def deleteFormaPago(id):
    dao = FormaPagoDao()
    try:
        deleted = dao.deleteFormaPago(id)
        if deleted:
            return jsonify(success=True, mensaje="Eliminada correctamente.", error=None), 200
        else:
            return jsonify(success=False, error="No encontrada o no eliminada."), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar forma de pago: {e}")
        return jsonify(success=False, error="Error interno."), 500
