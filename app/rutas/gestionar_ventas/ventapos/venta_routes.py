from flask import Blueprint, render_template

ventamod = Blueprint('ventamod', __name__, template_folder='templates')


@ventamod.route('/venta-pos')
def ventaPos():
    return render_template('venta-pos.html')