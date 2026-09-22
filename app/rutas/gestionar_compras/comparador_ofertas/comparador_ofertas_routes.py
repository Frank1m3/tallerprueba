from flask import Blueprint, render_template

cmpmod = Blueprint('cmpmod', __name__, template_folder='templates')


@cmpmod.route('/comparador-index')
def comparador_index():
    return render_template('comparador_index.html')
