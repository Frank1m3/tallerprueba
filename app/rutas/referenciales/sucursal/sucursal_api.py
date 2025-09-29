from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app import csrf

sucapi = Blueprint('sucapi', __name__)
dao = SucursalDao()

# ------------------- GET: lista completa -------------------
@sucapi.route('/sucursales', methods=['GET'])
def get_sucursales():
    try:
        lista = dao.getSucursales()
        return jsonify(success=True, data=lista, error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener sucursales: {e}")
        return jsonify(success=False, error="Error interno."), 500


# ------------------- GET: una sucursal por ID -------------------
@sucapi.route('/sucursales/<int:id_sucursal>', methods=['GET'])
def get_sucursal(id_sucursal):
    try:
        sucursal = dao.getSucursalById(id_sucursal)
        if sucursal:
            return jsonify(success=True, data=sucursal, error=None), 200
        return jsonify(success=False, error="Sucursal no encontrada."), 404
    except Exception as e:
        app.logger.error(f"Error al obtener sucursal: {e}")
        return jsonify(success=False, error="Error interno."), 500


# ------------------- POST: crear sucursal -------------------
@csrf.exempt
@sucapi.route('/sucursales', methods=['POST'])
def add_sucursal():
    data = request.get_json() or {}
    descripcion = data.get('descripcion', '').strip()
    if not descripcion:
        return jsonify(success=False, error="El campo descripcion es obligatorio."), 400

    # Campos opcionales
    activo = bool(data.get('activo', True))
    id_fiscal = data.get('id_fiscal')
    direccion = data.get('direccion')
    departamento = data.get('departamento')
    ciudad = data.get('ciudad')

    try:
        exito = dao.guardarSucursal(
            descripcion,
            activo,
            id_fiscal,
            direccion,
            departamento,
            ciudad
        )
        if exito:
            return jsonify(success=True, data=data, error=None), 201
        else:
            return jsonify(success=False, error="No se pudo guardar la sucursal."), 500
    except Exception as e:
        app.logger.error(f"Error al agregar sucursal: {e}")
        return jsonify(success=False, error="Error interno."), 500


# ------------------- PUT: actualizar sucursal -------------------
@csrf.exempt
@sucapi.route('/sucursales/<int:id_sucursal>', methods=['PUT'])
def update_sucursal(id_sucursal):
    data = request.get_json() or {}
    descripcion = data.get('descripcion', '').strip()
    if not descripcion:
        return jsonify(success=False, error="El campo descripcion es obligatorio."), 400

    activo = bool(data.get('activo', True))
    id_fiscal = data.get('id_fiscal')
    direccion = data.get('direccion')
    departamento = data.get('departamento')
    ciudad = data.get('ciudad')

    try:
        exito = dao.updateSucursal(
            id_sucursal,
            descripcion,
            activo,
            id_fiscal,
            direccion,
            departamento,
            ciudad
        )
        if exito:
            return jsonify(
                success=True,
                data={"id_sucursal": id_sucursal, **data},
                error=None
            ), 200
        else:
            return jsonify(success=False, error="Sucursal no encontrada o no se pudo actualizar."), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar sucursal: {e}")
        return jsonify(success=False, error="Error interno."), 500


# ------------------- DELETE: eliminar sucursal -------------------
@csrf.exempt
@sucapi.route('/sucursales/<int:id_sucursal>', methods=['DELETE'])
def delete_sucursal(id_sucursal):
    try:
        exito = dao.deleteSucursal(id_sucursal)
        if exito:
            return jsonify(success=True, mensaje=f"Sucursal {id_sucursal} eliminada.", error=None), 200
        else:
            return jsonify(success=False, error="Sucursal no encontrada."), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar sucursal: {e}")
        return jsonify(success=False, error="Error interno."), 500
