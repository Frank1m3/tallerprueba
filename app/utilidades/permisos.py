"""Control de acceso centralizado: autenticación + permisos por grupo, ventana y escenario.

Una sola verificación (before_request) protege páginas y APIs:
  - sin sesión            -> login (HTML) / 401 (API)
  - grupo 'administradores' -> acceso total
  - resto                 -> se busca la ventana por prefijo de ruta (paginas.pag_ruta /
                             paginas.pag_api) y se exige el escenario correspondiente:
        GET (página)   -> leer      POST -> insertar      PUT/PATCH -> editar
        DELETE o ruta con 'anular' -> borrar
    Las lecturas GET de las APIs (combos, listados de apoyo) quedan libres para cualquier
    usuario con sesión, porque otras ventanas las necesitan (ej. buscar productos en Compras).
  - rutas sin ventana asociada (dashboard, seguridad, etc.) solo exigen sesión.
"""
import time
from flask import session, request, jsonify, redirect, url_for, flash, render_template
from app.conexion.Conexion import Conexion

RUTAS_PUBLICAS = ('/login', '/logout', '/static', '/favicon.ico', '/cotizar/')   # /cotizar/: portal del proveedor (enlace personal)
GRUPO_ADMIN = 'administradores'
ACCIONES = ('leer', 'insertar', 'editar', 'borrar')
_TTL_SEGUNDOS = 30
_CACHE = {}            # grupo -> (momento, ventanas)
_CACHE_USUARIO = {}    # usu_id -> (momento, {pag_id: {accion: True/False}})  (solo pag_id con excepción)


def invalidar_cache(usu_id=None):
    """Sin usu_id (default): limpia todo (perfiles y excepciones individuales),
    como al guardar la matriz de un perfil. Con usu_id: solo esa persona,
    como al guardar sus permisos individuales."""
    if usu_id is None:
        _CACHE.clear()
        _CACHE_USUARIO.clear()
    else:
        _CACHE_USUARIO.pop(usu_id, None)


def ventanas_del_grupo(grupo):
    """Todas las ventanas activas con los permisos del grupo (False si no tiene fila)."""
    ahora = time.time()
    hit = _CACHE.get(grupo)
    if hit and ahora - hit[0] < _TTL_SEGUNDOS:
        return hit[1]

    con = Conexion().getConexion(); cur = con.cursor()
    try:
        cur.execute("""
            SELECT p.pag_id, p.pag_nombre, p.pag_ruta, p.pag_api, m.mod_des,
                   COALESCE(pe.leer, FALSE), COALESCE(pe.insertar, FALSE),
                   COALESCE(pe.editar, FALSE), COALESCE(pe.borrar, FALSE)
            FROM paginas p
            JOIN modulos m ON m.mod_id = p.mod_id
            LEFT JOIN permisos pe ON pe.pag_id = p.pag_id
                 AND pe.gru_id = (SELECT gru_id FROM grupos WHERE gru_des = %s)
            WHERE p.pag_estado IS TRUE
        """, (grupo,))
        ventanas = [{
            'id': r[0], 'nombre': r[1], 'ruta': r[2], 'api': r[3], 'modulo': r[4],
            'leer': r[5], 'insertar': r[6], 'editar': r[7], 'borrar': r[8]
        } for r in cur.fetchall()]
    finally:
        cur.close(); con.close()
    _CACHE[grupo] = (ahora, ventanas)
    return ventanas


def _excepciones_del_usuario(usu_id):
    """Excepciones individuales de un usuario: {pag_id: {accion: True/False}},
    solo con las acciones que de verdad se apartan del perfil (las NULL no entran)."""
    ahora = time.time()
    hit = _CACHE_USUARIO.get(usu_id)
    if hit and ahora - hit[0] < _TTL_SEGUNDOS:
        return hit[1]

    con = Conexion().getConexion(); cur = con.cursor()
    try:
        cur.execute("""
            SELECT pag_id, leer, insertar, editar, borrar
            FROM permisos_usuario WHERE usu_id = %s
        """, (usu_id,))
        excepciones = {}
        for pag_id, leer, insertar, editar, borrar in cur.fetchall():
            valores = {'leer': leer, 'insertar': insertar, 'editar': editar, 'borrar': borrar}
            excepciones[pag_id] = {a: v for a, v in valores.items() if v is not None}
    finally:
        cur.close(); con.close()
    _CACHE_USUARIO[usu_id] = (ahora, excepciones)
    return excepciones


def ventanas_del_usuario(usu_id, grupo):
    """Ventanas del perfil con las excepciones individuales del usuario aplicadas encima."""
    base = ventanas_del_grupo(grupo)
    if not usu_id:
        return base
    excepciones = _excepciones_del_usuario(usu_id)
    if not excepciones:
        return base
    resultado = []
    for v in base:
        extra = excepciones.get(v['id'])
        resultado.append({**v, **extra} if extra else v)
    return resultado


def _coincide(path, prefijo):
    return bool(prefijo) and (path == prefijo or path.startswith(prefijo + '/'))


def resolver_ventana(path, ventanas):
    """Devuelve (ventana, es_api) para la ruta, eligiendo el prefijo más específico."""
    mejor, mejor_len, es_api = None, -1, False
    for v in ventanas:
        for prefijo, api in ((v['ruta'], False), (v['api'], True)):
            if _coincide(path, prefijo) and len(prefijo) > mejor_len:
                mejor, mejor_len, es_api = v, len(prefijo), api
    return mejor, es_api


def accion_requerida(metodo, path):
    if metodo in ('GET', 'HEAD', 'OPTIONS'):
        return 'leer'
    if metodo == 'DELETE' or 'anular' in path.lower():
        return 'borrar'
    if metodo == 'POST':
        return 'insertar'
    return 'editar'


def es_admin():
    return session.get('grupo') == GRUPO_ADMIN


def puede(path, accion='leer'):
    """Para el menú y las plantillas: ¿el usuario actual puede hacer `accion` en esa ruta?"""
    if 'usuario_nombre' not in session or es_admin():
        return True
    ventana, _ = resolver_ventana(path, ventanas_del_usuario(session.get('usu_id'), session.get('grupo')))
    return True if ventana is None else bool(ventana[accion])


def permisos_de_la_ventana_actual():
    """Permisos del usuario para la ventana que se está viendo (o None si no aplica)."""
    if es_admin():
        return {a: True for a in ACCIONES}
    ventana, _ = resolver_ventana(request.path, ventanas_del_usuario(session.get('usu_id'), session.get('grupo')))
    return None if ventana is None else {a: ventana[a] for a in ACCIONES}


def _denegar(ventana, accion, es_api):
    from app.dao.seguridad.LogAccesoDao import LogAccesoDao
    LogAccesoDao().registrar(session.get('usuario_nombre'), 'ACCESO_DENEGADO', session.get('usu_id'),
                             f"{request.method} {request.path} — sin permiso '{accion}' en '{ventana['nombre']}'")
    texto = {'leer': 'ingresar a', 'insertar': 'agregar en', 'editar': 'modificar en', 'borrar': 'eliminar o anular en'}[accion]
    mensaje = f"No tiene permiso para {texto} «{ventana['nombre']}»."
    if es_api or request.is_json or request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': mensaje, 'data': None}), 403
    return render_template('403.html', mensaje=mensaje, ventana=ventana['nombre']), 403


def verificar_acceso():
    path = request.path
    if path == '/' or path.startswith(RUTAS_PUBLICAS):   # '/' redirige por sí misma según la sesión
        return None

    if 'usuario_nombre' not in session:
        if path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Sesión no válida o expirada. Debe iniciar sesión.'}), 401
        flash('Debe iniciar sesión para acceder al sistema.', 'warning')
        return redirect(url_for('login.login'))

    if es_admin():
        return None

    ventana, es_api = resolver_ventana(path, ventanas_del_usuario(session.get('usu_id'), session.get('grupo')))
    if ventana is None:
        return None

    accion = accion_requerida(request.method, path)
    if es_api and accion == 'leer':
        return None
    if not ventana[accion]:
        return _denegar(ventana, accion, es_api)
    return None


def registrar(app):
    app.before_request(verificar_acceso)

    @app.context_processor
    def inyectar_permisos():
        return {
            'puede': puede,
            'puede_ver': lambda path: puede(path, 'leer'),
            'permisos_ventana': permisos_de_la_ventana_actual,
        }
