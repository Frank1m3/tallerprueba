from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.cliente.ClienteDao import ClienteDao
from app.utilidades.validaciones import validar_texto, validar_ci, error_response, success_response
from app import csrf

cliapi = Blueprint('cliapi', __name__)

@cliapi.route('/clientes', methods=['GET'])
def getClientes():
    dao = ClienteDao()
    try:
        return success_response(data=dao.getClientes())
    except Exception as e:
        app.logger.error(f"Error al obtener clientes: {e}")
        return error_response("Error interno al obtener clientes.", 500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['GET'])
def getCliente(id_cliente):
    dao = ClienteDao()
    try:
        cliente = dao.getClienteById(id_cliente)
        if cliente:
            return success_response(data=cliente)
        return error_response("Cliente no encontrado.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener cliente: {e}")
        return error_response("Error interno.", 500)

@cliapi.route('/clientes', methods=['POST'])
@csrf.exempt
def addCliente():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    ok, msg, nombre = validar_texto(data.get('nombre'), "Nombre / Razón Social", min_len=2, max_len=100)
    if not ok:
        return error_response(msg, 400)

    ok, msg, cedula = validar_ci(data.get('cedula'), "Cédula / RUC")
    if not ok:
        return error_response(msg, 400)

    direccion = str(data.get('direccion', '') or '').strip().upper()
    if len(direccion) > 150:
        return error_response("La dirección no puede superar los 150 caracteres.", 400)

    telefono = str(data.get('telefono', '') or '').strip()
    if len(telefono) > 30:
        return error_response("El teléfono no puede superar los 30 caracteres.", 400)

    cta_cobrar = bool(data.get('cta_cobrar', False))

    dao = ClienteDao()
    try:
        exito, resultado = dao.guardarCliente(
            nombre=nombre.upper(),
            cedula=cedula,
            direccion=direccion,
            telefono=telefono,
            cta_cobrar=cta_cobrar
        )
        if exito:
            return success_response(data={'id_cliente': resultado}, status_code=201)
        return error_response(resultado or "No se pudo guardar el cliente.", 400)
    except Exception as e:
        app.logger.error(f"Error al agregar cliente: {e}")
        return error_response("Error interno al agregar cliente.", 500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['PUT'])
@csrf.exempt
def updateCliente(id_cliente):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    dao = ClienteDao()
    if not dao.getClienteById(id_cliente):
        return error_response("Cliente no encontrado.", 404)

    ok, msg, nombre = validar_texto(data.get('nombre'), "Nombre / Razón Social", min_len=2, max_len=100)
    if not ok:
        return error_response(msg, 400)

    ok, msg, cedula = validar_ci(data.get('cedula'), "Cédula / RUC")
    if not ok:
        return error_response(msg, 400)

    direccion = str(data.get('direccion', '') or '').strip().upper()
    if len(direccion) > 150:
        return error_response("La dirección no puede superar los 150 caracteres.", 400)

    telefono = str(data.get('telefono', '') or '').strip()
    if len(telefono) > 30:
        return error_response("El teléfono no puede superar los 30 caracteres.", 400)

    cta_cobrar = bool(data.get('cta_cobrar', False))

    try:
        exito, error = dao.updateCliente(
            id_cliente=id_cliente,
            nombre=nombre.upper(),
            cedula=cedula,
            direccion=direccion,
            telefono=telefono,
            cta_cobrar=cta_cobrar
        )
        if exito:
            return success_response(data={'id_cliente': id_cliente, 'nombre': nombre, 'cedula': cedula})
        return error_response(error or "No se pudo actualizar el cliente.", 400)
    except Exception as e:
        app.logger.error(f"Error al actualizar cliente: {e}")
        return error_response("Error interno al actualizar cliente.", 500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['DELETE'])
@csrf.exempt
def deleteCliente(id_cliente):
    dao = ClienteDao()
    try:
        if not dao.getClienteById(id_cliente):
            return error_response("Cliente no encontrado.", 404)

        exito, error = dao.deleteCliente(id_cliente)
        if exito:
            return success_response(mensaje=f"Cliente {id_cliente} eliminado correctamente.")
        return error_response(error or "No se puede eliminar el cliente porque posee ventas o cuentas asociadas.", 400)
    except Exception as e:
        app.logger.error(f"Error al eliminar cliente: {e}")
        return error_response("Error interno al eliminar cliente.", 500)