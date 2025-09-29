from flask import Blueprint, render_template

permod = Blueprint('persona', __name__, template_folder='templates')

@permod.route('/persona-index')
def personaIndex():
    return render_template('persona-index.html')