from flask import Blueprint, render_template
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao

dashmod = Blueprint('dashmod', __name__, template_folder='templates')


@dashmod.route('/')
def dashboard():
    sucursales = SucursalDao().getSucursales()
    return render_template('dashboard.html', sucursales=sucursales)


@dashmod.route('/riesgo-stock')
def riesgo_stock_index():
    sucursales = SucursalDao().getSucursales()
    return render_template('riesgo_stock_index.html', sucursales=sucursales)


@dashmod.route('/sin-stock')
def sin_stock_index():
    sucursales = SucursalDao().getSucursales()
    return render_template('sin_stock_index.html', sucursales=sucursales)
