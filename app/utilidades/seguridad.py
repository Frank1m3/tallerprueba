from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def login_required(f):
    """
    Decorador para proteger rutas.
    Si el usuario no ha iniciado sesión:
    - En peticiones HTML: Redirecciona al login con mensaje flash.
    - En peticiones API/AJAX: Retorna 401 Unauthorized en formato JSON.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_nombre' not in session and 'usuario_id' not in session:
            # Si es una petición JSON o API
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Sesión no válida o expirada. Debe iniciar sesión.'
                }), 401
            
            flash('Debe iniciar sesión para acceder a este módulo.', 'warning')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function
