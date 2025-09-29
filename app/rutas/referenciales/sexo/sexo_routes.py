from flask import Blueprint, render_template

sexomod = Blueprint('sexo', __name__, template_folder='templates')

@sexomod.route('/sexo-index')
def sexoIndex():
    return render_template('sexo-index.html')