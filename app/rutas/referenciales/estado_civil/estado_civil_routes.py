from flask import Blueprint, render_template

estmod = Blueprint('estado_civil', __name__, template_folder='templates')

@estmod.route('/estado_civil-index')
def estado_civilIndex():
    return render_template('estado_civil-index.html')