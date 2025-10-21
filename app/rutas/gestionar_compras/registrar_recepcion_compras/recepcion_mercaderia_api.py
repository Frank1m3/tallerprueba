from datetime import date, datetime
from flask import Blueprint, jsonify, request, current_app as app
from app.dao.gestionar_compras.registrar_recepcion_compras.RecepcionCompraDao import RecepcionDao
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compras_dto import RecepcionDto
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compra_detalle_dto import RecepcionDetalleDto
from app import csrf

api_v1 = "/api/v1"
modulo_compras = "/gestionar-compras"
rm_api = Blueprint('rm_api', __name__, url_prefix=f'{api_v1}{modulo_compras}/recepcion-mercaderias')

# ================================
# Obtener pedido por número
# ================================
@rm_api.route('/pedido/<nro_pedido>', methods=['GET'])
def get_pedido(nro_pedido):
    try:
        dao = RecepcionDao()
        pedido = dao.obtener_pedido_por_nro(nro_pedido)
        if not pedido:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404

        return jsonify({'success': True, 'data': pedido})

    except Exception as e:
        app.logger.error(f"Error al obtener pedido {nro_pedido}: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Crear nueva recepción
# ================================
@rm_api.route('/recepciones', methods=['POST'])
@csrf.exempt
def crear_recepcion():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

        id_funcionario = data.get('id_funcionario')
        if not id_funcionario:
            return jsonify({'success': False, 'error': 'El id_funcionario es obligatorio'}), 400

        detalle_objs = []
        for d in data.get('detalles', []):
            detalle_objs.append(RecepcionDetalleDto(
                item_code=d.get('item_code'),
                descripcion=d.get('descripcion', ''),
                cantidad_pedida=float(d.get('cantidad_pedida', 0)),
                cantidad_recibida=float(d.get('cantidad_recibida', 0))
            ))

        fecha_raw = data.get('fecha_recepcion')
        fecha_recepcion = datetime.strptime(fecha_raw, "%Y-%m-%d").date() if fecha_raw else date.today()

        recepcion_dto = RecepcionDto(
            nro_recepcion=data.get('nro_recepcion'),
            fecha_recepcion=fecha_recepcion,
            id_funcionario=id_funcionario,
            id_sucursal=data.get('id_sucursal'),
            id_deposito=data.get('id_deposito'),
            id_proveedor=data.get('id_proveedor'),
            id_pedido=data.get('id_pedido'),
            detalle_recepcion=detalle_objs
        )

        dao = RecepcionDao()
        exito = dao.agregar_recepcion(recepcion_dto)

        if exito:
            return jsonify({'success': True}), 201
        else:
            return jsonify({'success': False, 'error': 'No se pudo registrar la recepción'}), 500

    except Exception as e:
        app.logger.error(f"Error al crear recepción: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Confirmar recepción
# ================================
@rm_api.route('/recepciones/<int:id_recepcion>/confirmar', methods=['PUT'])
@csrf.exempt
def confirmar_recepcion(id_recepcion):
    try:
        dao = RecepcionDao()
        exito = dao.confirmar_recepcion(id_recepcion)
        return jsonify({'success': exito})
    except Exception as e:
        app.logger.error(f"Error al confirmar recepción {id_recepcion}: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500

# ================================
# Anular recepción
# ================================
@rm_api.route('/recepciones/<int:id_recepcion>/anular', methods=['PUT'])
@csrf.exempt
def anular_recepcion(id_recepcion):
    try:
        dao = RecepcionDao()
        exito = dao.anular_recepcion(id_recepcion)
        return jsonify({'success': exito})
    except Exception as e:
        app.logger.error(f"Error al anular recepción {id_recepcion}: {str(e)}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500
