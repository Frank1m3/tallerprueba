from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.apertura.AperturaDao import AperturaDao
from datetime import datetime

aperapi = Blueprint('aperapi', __name__)

@aperapi.route('/aperturas', methods=['GET'])
def getAperturas():
    aperturadao = AperturaDao()

    try:
        aperturas, ultimo_turno = aperturadao.getAperturas()  # Obtener aperturas y último turno
        siguiente_turno = ultimo_turno + 1 if ultimo_turno is not None else 1  # Calcular el siguiente turno

        return jsonify({
            'success': True,
            'data': aperturas,
            'siguiente_turno': siguiente_turno,  # Incluir el siguiente turno en la respuesta
            'error': None
        }), 200

    except Exception as e:
        app.logger.error(f"Error al obtener todas las aperturas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500


@aperapi.route('/aperturas/<int:id_apertura>', methods=['GET'])
def getApertura(id_apertura):
    aperturadao = AperturaDao()

    try:
        apertura = aperturadao.getAperturaById(id_apertura)

        if apertura:
            return jsonify({
                'success': True,
                'data': apertura,
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontró la apertura con el ID proporcionado.'
            }), 404

    except Exception as e:
        app.logger.error(f"Error al obtener apertura: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500
   

@aperapi.route('/aperturas', methods=['POST'])
def addApertura():
    data = request.get_json()
    aperturadao = AperturaDao()

    # Aseguramos que los campos requeridos estén presentes y no vacíos
    campos_requeridos = ['clave_fiscal', 'cajero', 'monto_inicial']

    for campo in campos_requeridos:
        if campo not in data or data[campo] is None or len(str(data[campo]).strip()) == 0:
            return jsonify({
                'success': False,
                'error': f'El campo {campo} es obligatorio y no puede estar vacío.'
            }), 400  # Devuelve error 400 si algún campo está vacío o no presente

    try:
        # Guardamos la apertura, la base de datos generará automáticamente el nro_turno
        result = aperturadao.guardarApertura(
            data['clave_fiscal'].strip().upper(),
            data['cajero'].strip(),
            data['monto_inicial']
        )

        if result is None:
            return jsonify({
                'success': False,
                'error': 'No se pudo realizar la apertura, verifique los datos ingresados.'
            }), 400  # Si no se pudo insertar, error 400

        # Obtener apertura guardada para traer el nro_turno y fecha registro actualizada
        apertura = aperturadao.getAperturaById(result['id_apertura'])

        # Si la apertura se guarda exitosamente, devolver el id generado + datos útiles
        return jsonify({
            'success': True,
            'data': {
                'id_apertura': result['id_apertura'],  # ID generado por la base de datos
                'clave_fiscal': data['clave_fiscal'].upper(),
                'cajero': data['cajero'].upper(),
                'monto_inicial': data['monto_inicial'],
                'nro_turno': apertura.get('nro_turno') if apertura else None,
                'registro': apertura.get('registro') if apertura else None
            },
            'error': None
        }), 201  # Código 201 para creación exitosa

    except Exception as e:
        # Si ocurre un error, verificar si es por funcionario dual
        if 'funcionario' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'Un funcionario no puede ser fiscal y cajero a la vez.'
            }), 400

        app.logger.error(f"Error al realizar apertura: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500  # Código 500 para errores internos del servidor



@aperapi.route('/aperturas/anular/<int:id_apertura>', methods=['PATCH'])
def anularApertura(id_apertura):
    aperturadao = AperturaDao()

    try:
        if aperturadao.anularApertura(id_apertura):
            return jsonify({
                'success': True,
                'mensaje': f'Apertura con ID {id_apertura} anulada correctamente.',
                'error': None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo anular la apertura o no se encontró el ID proporcionado.'
            }), 404

    except Exception as e:
        app.logger.error(f"Error al anular la apertura: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Ocurrió un error interno. Consulte con el administrador.'
        }), 500


# NUEVO ENDPOINT PARA OBTENER FECHA ACTUAL DEL SERVIDOR
@aperapi.route('/aperturas/fecha_actual', methods=['GET'])
def obtener_fecha_actual():
    try:
        now = datetime.now()
        fecha_str = now.strftime('%d/%m/%Y %H:%M:%S')
        return jsonify({'success': True, 'fecha_actual': fecha_str}), 200
    except Exception as e:
        app.logger.error(f"Error obteniendo fecha actual: {e}")
        return jsonify({'success': False, 'error': 'Error al obtener la fecha actual'}), 500
