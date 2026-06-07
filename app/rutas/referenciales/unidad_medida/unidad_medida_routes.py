from flask import Blueprint, render_template

unidadmedida_mod = Blueprint('unidadmedida', __name__, template_folder='templates')

@unidadmedida_mod.route('/unidad-medida')
def unidadMedidaIndex():
    return render_template('unidad-medida-index.html')
