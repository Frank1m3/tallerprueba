from flask import Blueprint, render_template

parametrocalidad_mod = Blueprint('parametrocalidad', __name__, template_folder='templates')

@parametrocalidad_mod.route('/parametro-calidad')
def parametroCalidadIndex():
    return render_template('parametro-calidad-index.html')
