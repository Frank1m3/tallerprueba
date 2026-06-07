from flask import Blueprint, render_template

arqueomod = Blueprint('arqueomod', __name__, template_folder='templates')

@arqueomod.route('/arqueo-index')
def arqueo_index():
    return render_template('arqueo-index.html')