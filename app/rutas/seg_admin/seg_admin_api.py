import re
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.dao.seguridad.PermisoDao import PermisoDao
from app.dao.seguridad.UsuarioDao import UsuarioDao
from app.dao.seguridad.LogAccesoDao import LogAccesoDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.utilidades.seguridad import admin_required
from app.utilidades.permisos import invalidar_cache
from app.rutas.seguridad.login_routes import validar_complejidad_clave
from app.utilidades.validaciones import validar_ci

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
    clave = d.get('usu_clave') or ''
    clave2 = d.get('usu_clave2') or ''
    if not _NICK.match(nick):
        return _err('El usuario debe tener entre 3 y 10 caracteres (letras, números, punto o guion bajo).')
    if email and not _EMAIL.match(email):
        return _err('El correo electrónico no tiene un formato válido.')
    if not d.get('gru_id'):
        return _err('Seleccioná el perfil.')
    if clave != clave2:
        return _err('Las dos contraseñas no coinciden.')
    problema = validar_complejidad_clave(clave)
    if problema:
        return _err(problema)

    fun_id = d.get('fun_id')
    nuevo_funcionario = d.get('funcionario_nuevo')
    detalle_funcionario = None
    if not fun_id:
        if not nuevo_funcionario:
            return _err('Seleccioná el funcionario, o cargá sus datos si todavía no está registrado.')
        nombres = (nuevo_funcionario.get('nombres') or '').strip()
        apellidos = (nuevo_funcionario.get('apellidos') or '').strip()
        car_id = nuevo_funcionario.get('car_id')
        if not nombres or not apellidos:
            return _err('Indicá nombre y apellido del funcionario nuevo.')
        if not car_id:
            return _err('Seleccioná el cargo del funcionario nuevo.')
        ok_ci, msg_ci, ci = validar_ci(nuevo_funcionario.get('ci'), 'Cédula')
        if not ok_ci:
            return _err(msg_ci)
        fun_id, error = FuncionarioDao().crear(nombres, apellidos, ci, int(car_id), session.get('usu_id'))
        if error:
            return _err(error)
        detalle_funcionario = f" — funcionario nuevo: {nombres} {apellidos} (CI {ci})"

    nuevo, error = UsuarioDao().crear(nick, generate_password_hash(clave), int(fun_id), int(d['gru_id']), email)
    if error:
        if detalle_funcionario:
            error += ' El funcionario ya quedó registrado: buscalo por su nombre para crear el usuario.'
        return _err(error)
    LogAccesoDao().registrar(nick, 'USUARIO_CREADO', nuevo,
                             f"Creado por {session.get('usuario_nombre')}{detalle_funcionario or ''}")
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


@segapi.route('/usuarios/<int:usu_id>/permisos', methods=['GET'])
@admin_required
def permisos_usuario_obtener(usu_id):
    usuario = UsuarioDao().obtener(usu_id)
    if not usuario:
        return _err('El usuario no existe.', 404)
    return jsonify({'success': True, 'data': PermisoDao().matriz_usuario(usu_id, usuario['gru_id'])})


@segapi.route('/usuarios/<int:usu_id>/permisos', methods=['PUT'])
@admin_required
def permisos_usuario_guardar(usu_id):
    usuario = UsuarioDao().obtener(usu_id)
    if not usuario:
        return _err('El usuario no existe.', 404)
    if usuario['grupo'] == 'administradores':
        return _err('Los administradores ya tienen acceso total: no admite excepciones.')
    filas = (request.get_json(silent=True) or {}).get('permisos')
    if not isinstance(filas, list):
        return _err('Datos de permisos inválidos.')
    if not PermisoDao().guardar_usuario(usu_id, filas):
        return _err('No se pudieron guardar los permisos individuales.', 500)
    invalidar_cache(usu_id)
    LogAccesoDao().registrar(usuario['usu_nick'], 'PERMISOS_INDIVIDUALES_MODIFICADOS', usu_id,
                             f"Modificados por {session.get('usuario_nombre')}")
    return jsonify({'success': True})
