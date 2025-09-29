from flask import Blueprint, render_template

# Blueprint para formas de pago
formapago_mod = Blueprint('formapago', __name__, template_folder='templates')

@formapago_mod.route('/formas-pago')
def formasPagoIndex():
    # Aquí podrías agregar lógica para pasar datos si es necesario
    return render_template('formas-pago-index.html')