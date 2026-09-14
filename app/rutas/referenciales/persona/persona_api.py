from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.persona.PersonaDao import PersonaDao
from app.utilidades.validaciones import (
    validar_texto, validar_ci, validar_fecha, validar_sexo,
    error_response, success_response
)
from app.utilidades.seguridad import login_required
from app import csrf

perapi = Blueprint('perapi', __name__)

@perapi.route('/personas', methods=['GET'])
def getPersonas():
    dao = PersonaDao()
    try:
        personas = dao.getPersonas()
        return jsonify(success=True, data=personas, error=None), 200
    except Exception as e:
        app.logger.error(f"Error al obtener personas: {e}")
        return error_response("Error interno al obtener personas.", 500)

@perapi.route('/personas/<int:id_persona>', methods=['GET'])
def getPersona(id_persona):
    dao = PersonaDao()
    try:
        persona = dao.getPersonaById(id_persona)
        if persona:
            return jsonify(success=True, data=persona, error=None), 200
        return error_response("Persona no encontrada.", 404)
    except Exception as e:
        app.logger.error(f"Error al obtener persona: {e}")
        return error_response("Error interno.", 500)

@perapi.route('/personas', methods=['POST'])
@csrf.exempt
def addPersona():
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    # Validar nombres
    ok, msg, nombres = validar_texto(data.get('nombres'), "Nombres", min_len=2, max_len=70, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    # Validar apellidos
    ok, msg, apellidos = validar_texto(data.get('apellidos'), "Apellidos", min_len=2, max_len=70, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    # Validar Cédula de Identidad (CI)
    ok, msg, ci = validar_ci(data.get('ci'), "Cédula de Identidad")
    if not ok:
        return error_response(msg, 400)

    # Validar Fecha de Nacimiento (no futura)
    ok, msg, fechanac = validar_fecha(data.get('fechanac'), "Fecha de Nacimiento", permitir_futuro=False)
    if not ok:
        return error_response(msg, 400)

    # Validar Sexo
    ok, msg, sexo = validar_sexo(data.get('sexo'), "Sexo")
    if not ok:
        return error_response(msg, 400)

    dao = PersonaDao()
    exito, res, code = dao.guardarPersona(nombres, apellidos, ci, fechanac, sexo)
    if exito:
        return jsonify({
            'success': True,
            'data': {
                'id_persona': res,
                'nombres': nombres,
                'apellidos': apellidos,
                'ci': ci,
                'fechanac': fechanac,
                'sexo': sexo
            },
            'error': None
        }), 201
    else:
        return error_response(res, code)

@perapi.route('/personas/<int:id_persona>', methods=['PUT'])
@csrf.exempt
def updatePersona(id_persona):
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return error_response("El cuerpo de la petición debe ser un objeto JSON válido.", 400)

    # Validar nombres
    ok, msg, nombres = validar_texto(data.get('nombres'), "Nombres", min_len=2, max_len=70, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    # Validar apellidos
    ok, msg, apellidos = validar_texto(data.get('apellidos'), "Apellidos", min_len=2, max_len=70, solo_letras=True)
    if not ok:
        return error_response(msg, 400)

    # Validar Cédula de Identidad (CI)
    ok, msg, ci = validar_ci(data.get('ci'), "Cédula de Identidad")
    if not ok:
        return error_response(msg, 400)

    # Validar Fecha de Nacimiento (no futura)
    ok, msg, fechanac = validar_fecha(data.get('fechanac'), "Fecha de Nacimiento", permitir_futuro=False)
    if not ok:
        return error_response(msg, 400)

    # Validar Sexo
    ok, msg, sexo = validar_sexo(data.get('sexo'), "Sexo")
    if not ok:
        return error_response(msg, 400)

    dao = PersonaDao()
    exito, res, code = dao.updatePersona(id_persona, nombres, apellidos, ci, fechanac, sexo)
    if exito:
        return jsonify({
            'success': True,
            'data': {
                'id_persona': id_persona,
                'nombres': nombres,
                'apellidos': apellidos,
                'ci': ci,
                'fechanac': fechanac,
                'sexo': sexo
            },
            'error': None
        }), 200
    else:
        return error_response(res, code)

@perapi.route('/personas/<int:id_persona>', methods=['DELETE'])
@csrf.exempt
def deletePersona(id_persona):
    dao = PersonaDao()
    exito, res, code = dao.deletePersona(id_persona)
    if exito:
        return jsonify(success=True, mensaje=f"Persona {id_persona} eliminada correctamente.", error=None), 200
    return error_response(res, code)
