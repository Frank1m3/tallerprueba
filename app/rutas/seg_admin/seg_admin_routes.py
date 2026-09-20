from flask import Blueprint, render_template
from app.dao.seguridad.PermisoDao import PermisoDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.utilidades.seguridad import admin_required

segmod = Blueprint('segmod', __name__, template_folder='templates')


@segmod.route('/usuarios')
@admin_required
def usuarios_index():
    return render_template('usuarios_index.html',
                           grupos=PermisoDao().grupos(),
                           funcionarios=FuncionarioDao().get_funcionarios())


@segmod.route('/permisos')
@admin_required
def permisos_index():
    return render_template('permisos_index.html', grupos=PermisoDao().grupos())
