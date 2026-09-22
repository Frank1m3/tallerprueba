from flask import Blueprint, render_template, flash, redirect, url_for
from app.dao.seguridad.PermisoDao import PermisoDao
from app.dao.seguridad.UsuarioDao import UsuarioDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.utilidades.seguridad import admin_required

segmod = Blueprint('segmod', __name__, template_folder='templates')


@segmod.route('/usuarios')
@admin_required
def usuarios_index():
    return render_template('usuarios_index.html', grupos=PermisoDao().grupos())


@segmod.route('/usuarios/nuevo')
@admin_required
def usuarios_nuevo():
    return render_template('usuario_form.html', modo='nuevo', usuario=None,
                           grupos=PermisoDao().grupos(),
                           funcionarios=FuncionarioDao().get_funcionarios(),
                           cargos=FuncionarioDao().get_cargos())


@segmod.route('/usuarios/<int:usu_id>/editar')
@admin_required
def usuarios_editar(usu_id):
    usuario = UsuarioDao().obtener(usu_id)
    if not usuario:
        flash('El usuario no existe.', 'danger')
        return redirect(url_for('segmod.usuarios_index'))
    return render_template('usuario_form.html', modo='editar', usuario=usuario,
                           grupos=PermisoDao().grupos(), funcionarios=[], cargos=[])


@segmod.route('/permisos')
@admin_required
def permisos_index():
    return render_template('permisos_index.html', grupos=PermisoDao().grupos())
