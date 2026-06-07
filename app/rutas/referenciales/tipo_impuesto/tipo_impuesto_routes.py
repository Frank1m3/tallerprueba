from flask import Blueprint, render_template

tipoimpuesto_mod = Blueprint('tipoimpuesto', __name__, template_folder='templates')

@tipoimpuesto_mod.route('/tipo-impuesto')
def tipoImpuestoIndex():
    return render_template('tipo-impuesto-index.html')
