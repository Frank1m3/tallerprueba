from flask import Blueprint, render_template

tipoitem_mod = Blueprint('tipoitem', __name__, template_folder='templates')

@tipoitem_mod.route('/tipo-item')
def tipoItemIndex():
    return render_template('tipo-item-index.html')
