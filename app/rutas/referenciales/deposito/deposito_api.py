from flask import Blueprint, request, jsonify, render_template, current_app as app
from app.dao.referenciales.deposito.DepositoDao import DepositoDao
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao  # corregido
from app import csrf

depoapi = Blueprint('depoapi', __name__)

# ---------------- Renderiza la página HTML con select de sucursales ----------------
@depoapi.route('/depositos/index', methods=['GET'])
def depositoIndex():
    suc_dao = SucursalDao()
    sucursales = suc_dao.getSucursales() or []
    return render_template('deposito-index.html', sucursales=sucursales)

# ---------------- Obtener todos los depósitos ----------------
@depoapi.route('/depositos', methods=['GET'])
def getDepositos():
    dao = DepositoDao()
    try:
        depositos = dao.getDepositos() or []
        return jsonify(success=True, data=depositos, error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos: {e}")
        return jsonify(success=False, error="Error interno."), 500

# ---------------- Obtener un depósito por ID ----------------
@depoapi.route('/depositos/<int:id_deposito>', methods=['GET'])
def getDeposito(id_deposito):
    dao = DepositoDao()
    try:
        deposito = dao.getDepositoById(id_deposito)
        if deposito:
            return jsonify(success=True, data=deposito, error=None), 200
        return jsonify(success=False, error="Depósito no encontrado."), 404
    except Exception as e:
        app.logger.error(f"Error al obtener depósito: {e}")
        return jsonify(success=False, error="Error interno."), 500

# ---------------- Crear nuevo depósito ----------------
@depoapi.route('/depositos', methods=['POST'])
@csrf.exempt
def addDeposito():
    data = request.get_json() or {}
    dao = DepositoDao()
    campos = ['descripcion', 'id_sucursal']

    for c in campos:
        if not data.get(c) or (isinstance(data.get(c), str) and data.get(c).strip() == ''):
            return jsonify(success=False, error=f'El campo {c} es obligatorio.'), 400

    try:
        id_deposito = dao.guardarDeposito(
            data['descripcion'].strip(),
            data['id_sucursal']
        )
        if id_deposito:
            return jsonify(success=True, data={'id_deposito': id_deposito}, error=None), 201
        return jsonify(success=False, error="No se pudo guardar el depósito."), 500
    except Exception as e:
        app.logger.error(f"Error al guardar depósito: {e}")
        return jsonify(success=False, error="Error interno."), 500

# ---------------- Actualizar depósito ----------------
@depoapi.route('/depositos/<int:id_deposito>', methods=['PUT'])
@csrf.exempt
def updateDeposito(id_deposito):
    data = request.get_json() or {}
    dao = DepositoDao()
    campos = ['descripcion', 'id_sucursal']

    for c in campos:
        if not data.get(c) or (isinstance(data.get(c), str) and data.get(c).strip() == ''):
            return jsonify(success=False, error=f'El campo {c} es obligatorio.'), 400

    try:
        actualizado = dao.updateDeposito(
            id_deposito,
            data['descripcion'].strip(),
            data['id_sucursal']
        )
        if actualizado:
            return jsonify(success=True, data=None, error=None), 200
        return jsonify(success=False, error="Depósito no encontrado o no actualizado."), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar depósito: {e}")
        return jsonify(success=False, error="Error interno."), 500

# ---------------- Eliminar depósito ----------------
@depoapi.route('/depositos/<int:id_deposito>', methods=['DELETE'])
@csrf.exempt
def deleteDeposito(id_deposito):
    dao = DepositoDao()
    try:
        eliminado = dao.deleteDeposito(id_deposito)
        if eliminado:
            return jsonify(success=True, mensaje=f"Depósito {id_deposito} eliminado.", error=None), 200
        return jsonify(success=False, error="Depósito no encontrado."), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar depósito: {e}")
        return jsonify(success=False, error="Error interno."), 500

# ---------------- Obtener depósitos por sucursal ----------------
@depoapi.route('/sucursal-depositos/<int:id_sucursal>', methods=['GET'])
def getDepositosPorSucursal(id_sucursal):
    dao = DepositoDao()
    try:
        depositos = dao.getDepositosPorSucursal(id_sucursal) or []
        depositos = [
            {
                'id_deposito': d.get('id_deposito'),
                'nombre_deposito': d.get('descripcion'),
                'stock': d.get('stock', 0)
            } for d in depositos
        ]
        return jsonify(success=True, data=depositos, error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener depósitos por sucursal: {e}")
        return jsonify(success=False, data=[], error="Error interno."), 500

# ---------------- Obtener stock por item y depósito ----------------
@depoapi.route('/stock/<int:id_deposito>/<int:id_item>', methods=['GET'])
def getStockPorItem(id_deposito, id_item):
    dao = DepositoDao()
    try:
        stock = dao.getStockPorItemYDeposito(id_item, id_deposito)
        return jsonify(success=True, stock=stock), 200
    except Exception as e:
        app.logger.error(f"Error al obtener stock del item: {e}")
        return jsonify(success=False, stock=0, error="Error interno"), 500
