from flask import Blueprint, request, jsonify, current_app as app
from app.dao.referenciales.persona.PersonaDao import PersonaDao
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
        return jsonify(success=False, error="Error interno."), 500

@perapi.route('/personas/<int:id_persona>', methods=['GET'])
def getPersona(id_persona):
    dao = PersonaDao()
    try:
        persona = dao.getPersonaById(id_persona)
        if persona:
            return jsonify(success=True, data=persona, error=None), 200
        return jsonify(success=False, error="Persona no encontrada."), 404
    except Exception as e:
        app.logger.error(f"Error al obtener persona: {e}")
        return jsonify(success=False, error="Error interno."), 500

@perapi.route('/personas', methods=['POST'])
@csrf.exempt
def addPersona():
    data = request.get_json() or {}
    dao = PersonaDao()
    campos = ['nombres', 'apellidos', 'ci', 'fechanac', 'sexo']

    for c in campos:
        if not data.get(c) or str(data.get(c)).strip() == '':
            return jsonify(success=False, error=f"El campo {c} es obligatorio."), 400

    try:
        exito = dao.guardarPersona(
            data['nombres'].strip(),
            data['apellidos'].strip(),
            data['ci'].strip(),
            data['fechanac'].strip(),
            data['sexo'].strip()
        )
        if exito:
            return jsonify(success=True, data=data, error=None), 201
        return jsonify(success=False, error="No se pudo guardar la persona."), 500
    except Exception as e:
        app.logger.error(f"Error al agregar persona: {e}")
        return jsonify(success=False, error="Error interno."), 500

@perapi.route('/personas/<int:id_persona>', methods=['PUT'])
@csrf.exempt
def updatePersona(id_persona):
    data = request.get_json() or {}
    dao = PersonaDao()
    campos = ['nombres', 'apellidos', 'ci', 'fechanac', 'sexo']

    for c in campos:
        if not data.get(c) or str(data.get(c)).strip() == '':
            return jsonify(success=False, error=f"El campo {c} es obligatorio."), 400

    try:
        exito = dao.updatePersona(
            id_persona,
            data['nombres'].strip(),
            data['apellidos'].strip(),
            data['ci'].strip(),
            data['fechanac'].strip(),
            data['sexo'].strip()
        )
        if exito:
            return jsonify(success=True, data=data, error=None), 200
        return jsonify(success=False, error="No encontrado o no se pudo actualizar."), 404
    except Exception as e:
        app.logger.error(f"Error al actualizar persona: {e}")
        return jsonify(success=False, error="Error interno."), 500

@perapi.route('/personas/<int:id_persona>', methods=['DELETE'])
@csrf.exempt
def deletePersona(id_persona):
    dao = PersonaDao()
    try:
        exito = dao.deletePersona(id_persona)
        if exito:
            return jsonify(success=True, mensaje=f"Persona {id_persona} eliminada.", error=None), 200
        return jsonify(success=False, error="Persona no encontrada."), 404
    except Exception as e:
        app.logger.error(f"Error al eliminar persona: {e}")
        return jsonify(success=False, error="Error interno."), 500
