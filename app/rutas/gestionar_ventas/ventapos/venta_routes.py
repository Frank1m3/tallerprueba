from flask import Blueprint, render_template
from app.utilidades.seguridad import login_required

ventamod = Blueprint('ventamod', __name__, template_folder='templates')

@ventamod.route('/venta-pos')
@login_required
def ventaPos():
    return render_template('venta-pos.html')
