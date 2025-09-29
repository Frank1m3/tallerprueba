from flask import Blueprint, render_template

sucmod = Blueprint('sucursal', __name__, template_folder='templates')

@sucmod.route('/sucursal-index')
def sucursalIndex():
    return render_template('sucursal-index.html')