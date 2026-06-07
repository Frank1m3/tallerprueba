from flask import Blueprint, render_template

marcatarjeta_mod = Blueprint('marcatarjeta', __name__, template_folder='templates')

@marcatarjeta_mod.route('/marca-tarjeta')
def marcaTarjetaIndex():
    return render_template('marca-tarjeta-index.html')
