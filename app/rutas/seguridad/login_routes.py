import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app as app
from werkzeug.security import check_password_hash, generate_password_hash
from app.dao.referenciales.usuario.login_dao import LoginDao
from app.utils.email_sender import enviar_codigo_2fa

logmod = Blueprint('login', __name__, template_folder='templates')

CODIGO_VIGENCIA_MINUTOS = 5
CODIGO_INTENTOS_MAXIMOS = 3  # falla en el intento 1 y 2 se puede reintentar; al fallar el 3ro (más de 2) vuelve al login
LOGIN_INTENTOS_MAXIMOS = 5  # al llegar a 5 intentos fallidos de contraseña, el usuario se bloquea en la BD


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
                flash('Usuario bloqueado por exceder el número de intentos permitidos. Contactá al administrador.', 'warning')
                return redirect(url_for('login.login'))

            password_hash_del_usuario = usuario_encontrado['usu_clave']

            # Verificar si la contraseña es correcta
            if check_password_hash(pwhash=password_hash_del_usuario, password=usuario_clave):
                login_dao.resetearIntentos(usuario_encontrado['usu_id'])

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
                if intentos >= LOGIN_INTENTOS_MAXIMOS:
                    flash('Contraseña incorrecta. Superaste el número de intentos permitidos: tu usuario fue bloqueado.', 'warning')
                else:
                    flash(f'Contraseña incorrecta. Intento {intentos} de {LOGIN_INTENTOS_MAXIMOS}.', 'warning')
                return redirect(url_for('login.login'))  # Redirigir al formulario de login

        else:
            # Usuario no encontrado
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
            flash('El código expiró. Iniciá sesión nuevamente.', 'warning')
            _limpiar_sesion_2fa()
            return redirect(url_for('login.login'))

        codigo_ingresado = request.form.get('codigo', '')

        if check_password_hash(session['tfa_codigo_hash'], codigo_ingresado):
            datos_sesion = session['tfa_datos_sesion']
            usu_id = session['tfa_usu_id']
            _limpiar_sesion_2fa()

            session.clear()
            session.permanent = True
            session['usu_id'] = usu_id
            session['usuario_nombre'] = datos_sesion['usuario_nombre']
            session['nombre_persona'] = datos_sesion['nombre_persona']
            session['grupo'] = datos_sesion['grupo']

            return redirect(url_for('login.inicio'))

        session['tfa_intentos'] += 1
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


@logmod.route('/logout')
def logout():
    session.clear()  # Limpiar cualquier sesión activa
    flash('Sesión cerrada', 'warning')
    return redirect(url_for('login.login'))  # Redirigir al formulario de login

@logmod.route('/')
def inicio():
    if 'usuario_nombre' in session:
        # Si el usuario está autenticado, redirigir a la página principal
        return render_template('base.html')
    else:
        # Si no está autenticado, redirigir al login
        return redirect(url_for('login.login'))
