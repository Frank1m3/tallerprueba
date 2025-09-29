from flask import Blueprint, render_template

cierremod = Blueprint('cierre', __name__, template_folder='templates')

@cierremod.route('/cierre-index')
def cierreIndex():
    return render_template('cierre-index.html')
