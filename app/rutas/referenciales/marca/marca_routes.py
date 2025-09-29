from flask import Blueprint, render_template

marcmod = Blueprint('marca', __name__, template_folder='templates')

@marcmod.route('/marca-index')
def marcaIndex():
    return render_template('marca-index.html')