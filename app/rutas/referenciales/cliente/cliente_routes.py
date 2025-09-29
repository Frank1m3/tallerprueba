from flask import Blueprint, render_template

climod = Blueprint('cliente', __name__, template_folder='templates')

@climod.route('/cliente-index')
def clienteIndex():
    return render_template('cliente-index.html')