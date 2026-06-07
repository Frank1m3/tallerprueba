from flask import Blueprint, render_template

grupo_mod = Blueprint('grupo', __name__, template_folder='templates')

@grupo_mod.route('/grupo')
def grupoIndex():
    return render_template('grupo-index.html')
