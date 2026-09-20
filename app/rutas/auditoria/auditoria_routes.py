from flask import Blueprint, render_template
from app.dao.auditoria.AuditoriaDao import AuditoriaDao
from app.utilidades.seguridad import admin_required

audmod = Blueprint('audmod', __name__, template_folder='templates')


@audmod.route('/')
@admin_required
def auditoria_index():
    tablas = AuditoriaDao().tablas_auditadas()
    return render_template('auditoria_index.html', tablas=tablas)


@audmod.route('/accesos')
@admin_required
def accesos_index():
    return render_template('accesos_index.html')
