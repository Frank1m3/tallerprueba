from flask import Blueprint, render_template

tipoetapas_mod = Blueprint('tipoetapas', __name__, template_folder='templates')

@tipoetapas_mod.route('/tipo-etapas')
def tipoEtapasIndex():
    return render_template('tipo-etapas-index.html')
