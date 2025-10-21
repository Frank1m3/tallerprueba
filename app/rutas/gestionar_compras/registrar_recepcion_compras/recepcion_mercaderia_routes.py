from flask import Blueprint, render_template
from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.referenciales.proveedor.ProveedorDao import ProveedorDao
from datetime import date

rm_mod = Blueprint('rm_mod', __name__, template_folder='templates')


# ==============================
# Función interna para cargar datos
# ==============================
def cargar_datos_recepcion():
    # DAOs
    sdao = SucursalDao()
    fdao = FuncionarioDao()
    pdao = ProveedorDao()

    # Listas para selects
    sucursales = sdao.getSucursales()
    funcionarios = fdao.get_funcionarios()
    proveedores = pdao.getProveedores()

    # Fecha actual
    fecha_actual = date.today().strftime("%Y-%m-%d")

    return {
        'sucursales': sucursales,
        'funcionarios': funcionarios,
        'proveedores': proveedores,
        'fecha_actual': fecha_actual
    }


# ==============================
# Página principal de recepción
# ==============================
@rm_mod.route('/recepcion-mercaderia')
@rm_mod.route('/recepcion-mercaderia/recepcion-index')
def recepcion_mercaderia():
    data = cargar_datos_recepcion()
    return render_template('recepcion_mercaderia.html', **data)
