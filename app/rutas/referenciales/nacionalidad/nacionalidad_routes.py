from flask import Blueprint, render_template

nacmod = Blueprint('nacionalidad', __name__, template_folder='templates')

@nacmod.route('/nacionalidad-index')
def nacionalidadIndex():
    return render_template('nacionalidad-index.html')