import re
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.dao.seguridad.PermisoDao import PermisoDao
from app.dao.seguridad.UsuarioDao import UsuarioDao
from app.dao.seguridad.LogAccesoDao import LogAccesoDao
from app.utilidades.seguridad import admin_required
from app.utilidades.permisos import invalidar_cache
from app.rutas.seguridad.login_routes import validar_complejidad_clave

segapi = Blueprint('segapi', __name__)

_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_NICK = re.compile(r'^[A-Za-z0-9_.]{3,10}$')


def _err(msg, code=400):
    return jsonify({'success': False, 'error': msg}), code


@segapi.route('/usuarios', methods=['GET'])
@admin_required
def usuarios_listar():
    return jsonify({'success': True, 'data': UsuarioDao().listar()})


@segapi.route('/usuarios', methods=['POST'])
@admin_required
def usuarios_crear():
    d = request.get_json(silent=True) or {}
    nick = (d.get('usu_nick') or '').strip()
    email = (d.get('usu_email') or '').strip()
    if not _NICK.match(nick):
        return _err('El usuario debe tener entre 3 y 10 caracteres (letras, números, punto o guion bajo).')
    if email and not _EMAIL.match(email):
        return _err('El correo electrónico no tiene un formato válido.')
    if not d.get('fun_id') or not d.get('gru_id'):
        return _err('Seleccioná el funcionario y el perfil.')
    problema = validar_complejidad_clave(d.get('usu_clave') or '')
    if problema:
        return _err(problema)

    nuevo, error = UsuarioDao().crear(nick, generate_password_hash(d['usu_clave']), int(d['fun_id']), int(d['gru_id']), email)
    if error:
        return _err(error)
    return jsonify({'success': True, 'data': {'usu_id': nuevo}}), 201


@segapi.route('/usuarios/<int:usu_id>', methods=['PUT'])
@admin_required
def usuarios_actualizar(usu_id):
    d = request.get_json(silent=True) or {}
    email = (d.get('usu_email') or '').strip()
    if email and not _EMAIL.match(email):
        return _err('El correo electrónico no tiene un formato válido.')
    if not d.get('gru_id'):
        return _err('Seleccioná el perfil.')
    estado = bool(d.get('usu_estado'))

    # Evita que un administrador se bloquee a sí mismo o se quite el perfil de administrador
    if usu_id == session.get('usu_id'):
        propio = next((u for u in UsuarioDao().listar() if u['usu_id'] == usu_id), None)
        if not estado or (propio and int(d['gru_id']) != propio['gru_id']):
            return _err('No podés desactivar tu propio usuario ni cambiar tu propio perfil.')

    if not UsuarioDao().actualizar(usu_id, int(d['gru_id']), email, estado):
        return _err('No se pudo actualizar el usuario.', 500)
    if estado:
        LogAccesoDao().registrar(UsuarioDao().nick(usu_id), 'CUENTA_ACTUALIZADA', usu_id,
                                 f"Actualizada por {session.get('usuario_nombre')} (activa, intentos reiniciados)")
    return jsonify({'success': True})


@segapi.route('/usuarios/<int:usu_id>/clave', methods=['PUT'])
@admin_required
def usuarios_clave(usu_id):
    d = request.get_json(silent=True) or {}
    problema = validar_complejidad_clave(d.get('clave') or '')
    if problema:
        return _err(problema)
    from app.dao.referenciales.usuario.login_dao import LoginDao
    if not LoginDao().actualizarClave(usu_id, generate_password_hash(d['clave'])):
        return _err('No se pudo actualizar la contraseña.', 500)
    LogAccesoDao().registrar(UsuarioDao().nick(usu_id), 'CLAVE_RESTABLECIDA', usu_id,
                             f"Contraseña restablecida por el administrador {session.get('usuario_nombre')}")
    return jsonify({'success': True})


@segapi.route('/permisos/<int:gru_id>', methods=['GET'])
@admin_required
def permisos_obtener(gru_id):
    return jsonify({'success': True, 'data': PermisoDao().matriz(gru_id)})


@segapi.route('/permisos/<int:gru_id>', methods=['PUT'])
@admin_required
def permisos_guardar(gru_id):
    filas = (request.get_json(silent=True) or {}).get('permisos')
    if not isinstance(filas, list):
        return _err('Datos de permisos inválidos.')
    if not PermisoDao().guardar(gru_id, filas):
        return _err('No se pudieron guardar los permisos.', 500)
    invalidar_cache()
    return jsonify({'success': True})
