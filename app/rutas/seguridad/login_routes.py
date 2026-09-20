import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from app.dao.referenciales.usuario.login_dao import LoginDao
from app.utils.email_sender import enviar_codigo_2fa, enviar_alerta_acceso
from app.dao.seguridad.LogAccesoDao import LogAccesoDao

logmod = Blueprint('login', __name__, template_folder='templates')

CODIGO_VIGENCIA_MINUTOS = 5
CODIGO_INTENTOS_MAXIMOS = 3  # falla en el intento 1 y 2 se puede reintentar; al fallar el 3ro (más de 2) vuelve al login
LOGIN_INTENTOS_MAXIMOS = 3  # al llegar a 3 intentos fallidos de contraseña, el usuario se bloquea en la BD


log_acceso = LogAccesoDao()


def validar_complejidad_clave(clave: str):
    """Devuelve None si la contraseña es válida, o un mensaje con lo que falta."""
    if len(clave) < 8:
        return 'La contraseña debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', clave):
        return 'La contraseña debe incluir al menos una letra mayúscula.'
    if not re.search(r'[a-z]', clave):
        return 'La contraseña debe incluir al menos una letra minúscula.'
    if not re.search(r'\d', clave):
        return 'La contraseña debe incluir al menos un número.'
    return None


def _alertar_intento_fallido(usuario, intentos):
    """Alerta por correo al dueño de la cuenta (y a los administradores si se bloqueó)."""
    ip = request.remote_addr
    cuando = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    bloqueado = intentos >= LOGIN_INTENTOS_MAXIMOS
    destinatarios = [usuario.get('usu_email')]
    if bloqueado:
        destinatarios += log_acceso.emails_administradores()
        asunto = f"Cuenta bloqueada: {usuario['usu_nick']}"
        cuerpo = (f"La cuenta '{usuario['usu_nick']}' fue bloqueada tras {intentos} intentos fallidos de acceso.\n"
                  f"Último intento: {cuando} desde la IP {ip}.\n\n"
                  "Un administrador debe reactivarla. Si no fuiste vos, revisá la ventana de intentos de acceso.")
    else:
        asunto = f"Intento de acceso fallido en tu cuenta ({intentos} de {LOGIN_INTENTOS_MAXIMOS})"
        cuerpo = (f"Se registró un intento fallido de acceso a la cuenta '{usuario['usu_nick']}'.\n"
                  f"Fecha y hora: {cuando}\nIP: {ip}\n"
                  f"Intento {intentos} de {LOGIN_INTENTOS_MAXIMOS}: al llegar al máximo la cuenta se bloquea.\n\n"
                  "Si no fuiste vos, avisá a un administrador.")
    log_acceso.enviar_alerta_async(destinatarios, asunto, cuerpo)


def _generar_y_enviar_codigo(usuario_encontrado):
    codigo = f"{secrets.randbelow(1000000):06d}"
    session['tfa_usu_id'] = usuario_encontrado['usu_id']
    session['tfa_codigo_hash'] = generate_password_hash(codigo)
    session['tfa_expira'] = (datetime.utcnow() + timedelta(minutes=CODIGO_VIGENCIA_MINUTOS)).isoformat()
    session['tfa_intentos'] = 0
    session['tfa_datos_sesion'] = {
        'usuario_nombre': usuario_encontrado['usu_nick'],
        'nombre_persona': usuario_encontrado['nombre_persona'],
        'grupo': usuario_encontrado['grupo'],
    }
    return enviar_codigo_2fa(usuario_encontrado['usu_email'], codigo)


def _limpiar_sesion_2fa():
    for clave in ('tfa_usu_id', 'tfa_codigo_hash', 'tfa_expira', 'tfa_intentos', 'tfa_datos_sesion'):
        session.pop(clave, None)


@logmod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Recuperar los datos del formulario
        usuario_nombre = request.form['usuario_nombre']
        usuario_clave = request.form['usuario_clave']

        # Instanciar el objeto LoginDao y buscar el usuario en la base de datos
        login_dao = LoginDao()
        usuario_encontrado = login_dao.buscarUsuario(usuario_nombre)

        # Verificar si el usuario fue encontrado
        if usuario_encontrado and 'usu_nick' in usuario_encontrado:
            if not usuario_encontrado['usu_estado']:
                log_acceso.registrar(usuario_nombre, 'USUARIO_BLOQUEADO', usuario_encontrado['usu_id'], 'Intento de acceso a una cuenta bloqueada')
                flash('Usuario bloqueado por exceder el número de intentos permitidos. Contactá al administrador.', 'warning')
                return redirect(url_for('login.login'))

            password_hash_del_usuario = usuario_encontrado['usu_clave']

            # Verificar si la contraseña es correcta
            if check_password_hash(pwhash=password_hash_del_usuario, password=usuario_clave):
                login_dao.resetearIntentos(usuario_encontrado['usu_id'])
                log_acceso.registrar(usuario_nombre, 'LOGIN_OK', usuario_encontrado['usu_id'], 'Contraseña correcta; pendiente verificación en dos pasos')

                if not usuario_encontrado.get('usu_email'):
                    flash('Tu usuario no tiene un correo configurado para la verificación en dos pasos. Contactá al administrador.', 'warning')
                    return redirect(url_for('login.login'))

                if not _generar_y_enviar_codigo(usuario_encontrado):
                    flash('No se pudo enviar el código de verificación. Intentá nuevamente en unos minutos.', 'warning')
                    _limpiar_sesion_2fa()
                    return redirect(url_for('login.login'))

                return redirect(url_for('login.verificar'))

            else:
                # Contraseña incorrecta: registrar el intento y bloquear si corresponde
                intentos = login_dao.registrarIntentoFallido(usuario_encontrado['usu_id'], LOGIN_INTENTOS_MAXIMOS)
                log_acceso.registrar(usuario_nombre, 'LOGIN_FALLIDO', usuario_encontrado['usu_id'], f'Contraseña incorrecta (intento {intentos} de {LOGIN_INTENTOS_MAXIMOS})')
                if intentos >= LOGIN_INTENTOS_MAXIMOS:
                    log_acceso.registrar(usuario_nombre, 'CUENTA_BLOQUEADA', usuario_encontrado['usu_id'], 'Bloqueada por exceder el máximo de intentos')
                _alertar_intento_fallido(usuario_encontrado, intentos)
                if intentos >= LOGIN_INTENTOS_MAXIMOS:
                    flash('Contraseña incorrecta. Superaste el número de intentos permitidos: tu usuario fue bloqueado.', 'warning')
                else:
                    flash(f'Contraseña incorrecta. Intento {intentos} de {LOGIN_INTENTOS_MAXIMOS}.', 'warning')
                return redirect(url_for('login.login'))  # Redirigir al formulario de login

        else:
            # Usuario no encontrado
            log_acceso.registrar(usuario_nombre, 'USUARIO_INEXISTENTE', None, 'El usuario ingresado no existe')
            flash('Error de inicio, no existe este usuario')
            return redirect(url_for('login.login'))  # Redirigir al formulario de login

    elif request.method == 'GET':
        # Si la solicitud es GET, se muestra el formulario de login
        return render_template('login.html')


@logmod.route('/login/verificar', methods=['GET', 'POST'])
def verificar():
    if 'tfa_usu_id' not in session:
        return redirect(url_for('login.login'))

    if request.method == 'POST':
        expira = datetime.fromisoformat(session['tfa_expira'])
        if datetime.utcnow() > expira:
            log_acceso.registrar(session['tfa_datos_sesion']['usuario_nombre'], '2FA_EXPIRADO', session['tfa_usu_id'], 'El código de verificación expiró')
            flash('El código expiró. Iniciá sesión nuevamente.', 'warning')
            _limpiar_sesion_2fa()
            return redirect(url_for('login.login'))

        codigo_ingresado = request.form.get('codigo', '')

        if check_password_hash(session['tfa_codigo_hash'], codigo_ingresado):
            datos_sesion = session['tfa_datos_sesion']
            usu_id = session['tfa_usu_id']
            _limpiar_sesion_2fa()
            log_acceso.registrar(datos_sesion['usuario_nombre'], '2FA_OK', usu_id, 'Acceso completo al sistema')

            session.clear()
            session.permanent = True
            session['usu_id'] = usu_id
            session['usuario_nombre'] = datos_sesion['usuario_nombre']
            session['nombre_persona'] = datos_sesion['nombre_persona']
            session['grupo'] = datos_sesion['grupo']

            return redirect(url_for('login.inicio'))

        session['tfa_intentos'] += 1
        log_acceso.registrar(session['tfa_datos_sesion']['usuario_nombre'], '2FA_FALLIDO', session['tfa_usu_id'], f"Código incorrecto (intento {session['tfa_intentos']} de {CODIGO_INTENTOS_MAXIMOS})")
        if session['tfa_intentos'] >= CODIGO_INTENTOS_MAXIMOS:
            flash('Superaste el número de intentos permitidos. Iniciá sesión nuevamente.', 'warning')
            _limpiar_sesion_2fa()
            return redirect(url_for('login.login'))

        flash('Código incorrecto', 'warning')
        return redirect(url_for('login.verificar'))

    return render_template('verificar_2fa.html')


@logmod.route('/login/verificar/reenviar')
def reenviar():
    if 'tfa_usu_id' not in session:
        return redirect(url_for('login.login'))

    login_dao = LoginDao()
    usuario_encontrado = login_dao.buscarUsuarioPorId(session['tfa_usu_id'])
    if not usuario_encontrado or not usuario_encontrado.get('usu_email'):
        flash('No se pudo reenviar el código. Iniciá sesión nuevamente.', 'warning')
        _limpiar_sesion_2fa()
        return redirect(url_for('login.login'))

    if _generar_y_enviar_codigo(usuario_encontrado):
        flash('Te enviamos un nuevo código.', 'warning')
    else:
        flash('No se pudo enviar el código de verificación. Intentá nuevamente en unos minutos.', 'warning')

    return redirect(url_for('login.verificar'))


RECUPERACION_VIGENCIA_MINUTOS = 10
RECUPERACION_INTENTOS_MAXIMOS = 3
_CLAVES_RECUPERACION = ('rec_usu_id', 'rec_usuario', 'rec_codigo_hash', 'rec_expira', 'rec_intentos')


@logmod.route('/login/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        usuario_nombre = request.form.get('usuario_nombre', '').strip()
        usuario = LoginDao().buscarUsuario(usuario_nombre) if usuario_nombre else None

        codigo = f"{secrets.randbelow(1000000):06d}"
        usu_id = 0
        if usuario and usuario.get('usu_email') and usuario['usu_estado']:
            usu_id = usuario['usu_id']
            enviar_alerta_acceso(
                [usuario['usu_email']],
                'Recuperación de contraseña',
                f"Tu código para restablecer la contraseña es: {codigo}\n\n"
                f"Vence en {RECUPERACION_VIGENCIA_MINUTOS} minutos. Si no lo solicitaste, ignorá este mensaje.")
            log_acceso.registrar(usuario_nombre, 'RECUPERACION_SOLICITADA', usu_id, 'Se envió un código de recuperación al correo')
        else:
            log_acceso.registrar(usuario_nombre, 'RECUPERACION_FALLIDA', None, 'Usuario inexistente, bloqueado o sin correo')

        # Misma respuesta exista o no el usuario, para no revelar qué usuarios están registrados.
        session['rec_usu_id'] = usu_id
        session['rec_usuario'] = usuario_nombre
        session['rec_codigo_hash'] = generate_password_hash(codigo)
        session['rec_expira'] = (datetime.utcnow() + timedelta(minutes=RECUPERACION_VIGENCIA_MINUTOS)).isoformat()
        session['rec_intentos'] = 0
        flash('Si el usuario existe, enviamos un código de verificación a su correo registrado.', 'info')
        return redirect(url_for('login.restablecer'))

    return render_template('recuperar.html')


@logmod.route('/login/recuperar/restablecer', methods=['GET', 'POST'])
def restablecer():
    if 'rec_codigo_hash' not in session:
        return redirect(url_for('login.recuperar'))

    if request.method == 'POST':
        usuario_nombre = session.get('rec_usuario', '')
        if datetime.utcnow() > datetime.fromisoformat(session['rec_expira']):
            flash('El código expiró. Solicitá uno nuevo.', 'warning')
            return redirect(url_for('login.recuperar'))

        codigo = request.form.get('codigo', '')
        nueva = request.form.get('nueva_clave', '')
        confirmar = request.form.get('confirmar_clave', '')

        if not session.get('rec_usu_id') or not check_password_hash(session['rec_codigo_hash'], codigo):
            session['rec_intentos'] += 1
            log_acceso.registrar(usuario_nombre, 'RECUPERACION_FALLIDA', session.get('rec_usu_id') or None, 'Código de recuperación incorrecto')
            if session['rec_intentos'] >= RECUPERACION_INTENTOS_MAXIMOS:
                for k in _CLAVES_RECUPERACION:
                    session.pop(k, None)
                flash('Superaste el número de intentos. Solicitá un nuevo código.', 'warning')
                return redirect(url_for('login.recuperar'))
            flash('Código incorrecto.', 'warning')
            return redirect(url_for('login.restablecer'))

        if nueva != confirmar:
            flash('Las contraseñas no coinciden.', 'warning')
            return redirect(url_for('login.restablecer'))
        error = validar_complejidad_clave(nueva)
        if error:
            flash(error, 'warning')
            return redirect(url_for('login.restablecer'))

        usu_id = session['rec_usu_id']
        if LoginDao().actualizarClave(usu_id, generate_password_hash(nueva)):
            log_acceso.registrar(usuario_nombre, 'CLAVE_RESTABLECIDA', usu_id, 'Contraseña restablecida mediante código por correo')
            for k in _CLAVES_RECUPERACION:
                session.pop(k, None)
            flash('Contraseña actualizada. Ya podés iniciar sesión.', 'success')
            return redirect(url_for('login.login'))
        flash('No se pudo actualizar la contraseña. Intentá nuevamente.', 'warning')
        return redirect(url_for('login.restablecer'))

    return render_template('restablecer.html')


@logmod.route('/logout')
def logout():
    if 'usuario_nombre' in session:
        log_acceso.registrar(session['usuario_nombre'], 'LOGOUT', session.get('usu_id'), 'Cierre de sesión')
    session.clear()  # Limpiar cualquier sesión activa
    flash('Sesión cerrada', 'warning')
    return redirect(url_for('login.login'))  # Redirigir al formulario de login

@logmod.route('/')
def inicio():
    if 'usuario_nombre' in session:
        # Si el usuario está autenticado, redirigir al dashboard
        return redirect(url_for('dashmod.dashboard'))
    else:
        # Si no está autenticado, redirigir al login
        return redirect(url_for('login.login'))
