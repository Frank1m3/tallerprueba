from flask import Blueprint, render_template

paismod = Blueprint('pais', __name__, template_folder='templates')

@paismod.route('/pais-index')
def paisIndex():
    return render_template('pais-index.html')