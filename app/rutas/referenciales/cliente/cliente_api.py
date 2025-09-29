from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.cliente.ClienteDao import ClienteDao
from app import csrf  # Importamos csrf para la protección

cliapi = Blueprint('cliapi', __name__)

def response_json(success, data=None, error=None, status_code=200):
    return jsonify({
        'success': success,
        'data': data,
        'error': error
    }), status_code

@cliapi.route('/clientes', methods=['GET'])
def getClientes():
    dao = ClienteDao()
    try:
        clientes = dao.getClientes()
        return response_json(True, clientes)
    except Exception as e:
        app.logger.error(f"Error al obtener clientes: {e}")
        return response_json(False, error='Error interno.', status_code=500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['GET'])
def getCliente(id_cliente):
    dao = ClienteDao()
    try:
        cliente = dao.getClienteById(id_cliente)
        if cliente:
            return response_json(True, cliente)
        return response_json(False, error='Cliente no encontrado.', status_code=404)
    except Exception as e:
        app.logger.error(f"Error al obtener cliente: {e}")
        return response_json(False, error='Error interno.', status_code=500)

@cliapi.route('/clientes', methods=['POST'])
@csrf.exempt
def addCliente():
    data = request.get_json() or {}
    dao = ClienteDao()
    campos_requeridos = ['nombre', 'apellido', 'cedula', 'direccion', 'telefono']

    for campo in campos_requeridos:
        if campo not in data or not str(data[campo]).strip():
            return response_json(False, error=f'El campo {campo} es obligatorio.', status_code=400)

    try:
        exito, error = dao.guardarCliente(
            data['nombre'].strip().upper(),
            data['apellido'].strip().upper(),
            data['cedula'].strip(),
            data['direccion'].strip().upper(),
            data['telefono'].strip()
        )
        if exito:
            return response_json(True, data=data, status_code=201)
        else:
            return response_json(False, error=error or "No se pudo guardar el cliente.", status_code=500)
    except Exception as e:
        app.logger.error(f"Error al agregar cliente: {e}")
        return response_json(False, error='Error interno.', status_code=500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['PUT'])
@csrf.exempt
def updateCliente(id_cliente):
    data = request.get_json() or {}
    dao = ClienteDao()
    campos_requeridos = ['nombre', 'apellido', 'cedula', 'direccion', 'telefono']

    for campo in campos_requeridos:
        if campo not in data or not str(data[campo]).strip():
            return response_json(False, error=f'El campo {campo} es obligatorio.', status_code=400)

    try:
        cliente_existente = dao.getClienteById(id_cliente)
        if not cliente_existente:
            return response_json(False, error='Cliente no encontrado.', status_code=404)

        exito, error = dao.updateCliente(
            id_cliente,
            data['nombre'].strip().upper(),
            data['apellido'].strip().upper(),
            data['cedula'].strip(),
            data['direccion'].strip().upper(),
            data['telefono'].strip()
        )
        if exito:
            return response_json(True, data=data)
        else:
            return response_json(False, error=error or "No se pudo actualizar el cliente.", status_code=500)

    except Exception as e:
        app.logger.error(f"Error al actualizar cliente: {e}")
        return response_json(False, error='Error interno.', status_code=500)

@cliapi.route('/clientes/<int:id_cliente>', methods=['DELETE'])
@csrf.exempt
def deleteCliente(id_cliente):
    dao = ClienteDao()
    try:
        cliente_existente = dao.getClienteById(id_cliente)
        if not cliente_existente:
            return response_json(False, error='Cliente no encontrado.', status_code=404)

        exito, error = dao.deleteCliente(id_cliente)
        if exito:
            return response_json(True, data={'mensaje': f'Cliente {id_cliente} eliminado correctamente.'})
        else:
            return response_json(False, error=error or "No se pudo eliminar el cliente.", status_code=500)

    except Exception as e:
        app.logger.error(f"Error al eliminar cliente: {e}")
        return response_json(False, error='Error interno.', status_code=500)
