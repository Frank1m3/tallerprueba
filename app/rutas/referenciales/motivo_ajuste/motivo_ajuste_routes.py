from flask import Blueprint, render_template

motivoajuste_mod = Blueprint('motivoajuste', __name__, template_folder='templates')

@motivoajuste_mod.route('/motivo-ajuste')
def motivoAjusteIndex():
    return render_template('motivo-ajuste-index.html')
