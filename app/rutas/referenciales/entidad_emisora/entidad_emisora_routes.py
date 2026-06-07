from flask import Blueprint, render_template

entidademisora_mod = Blueprint('entidademisora', __name__, template_folder='templates')

@entidademisora_mod.route('/entidad-emisora')
def entidadEmisoraIndex():
    return render_template('entidad-emisora-index.html')
