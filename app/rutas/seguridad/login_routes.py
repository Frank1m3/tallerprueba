from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app as app
from werkzeug.security import check_password_hash
from app.dao.referenciales.usuario.login_dao import LoginDao

logmod = Blueprint('login', __name__, template_folder='templates')

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
            password_hash_del_usuario = usuario_encontrado['usu_clave']
            
            # Verificar si la contraseña es correcta
            if check_password_hash(pwhash=password_hash_del_usuario, password=usuario_clave):
                # Login exitoso, crear sesión
                session.clear()  # Limpiar cualquier sesión previa
                session.permanent = True
                session['usu_id'] = usuario_encontrado['usu_id']
                session['usuario_nombre'] = usuario_nombre
                session['nombre_persona'] = usuario_encontrado['nombre_persona']
                session['grupo'] = usuario_encontrado['grupo']
                
                return redirect(url_for('login.inicio'))  # Redirigir al inicio

            else:
                # Contraseña incorrecta
                flash('Contraseña incorrecta', 'warning')
                return redirect(url_for('login.login'))  # Redirigir al formulario de login

        else:
            # Usuario no encontrado
            flash('Error de inicio, no existe este usuario')
            return redirect(url_for('login.login'))  # Redirigir al formulario de login

    elif request.method == 'GET':
        # Si la solicitud es GET, se muestra el formulario de login
        return render_template('login.html')

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
