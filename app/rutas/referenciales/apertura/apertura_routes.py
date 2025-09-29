from flask import Blueprint, render_template

apermod = Blueprint('apertura', __name__, template_folder='templates')

@apermod.route('/apertura-index')
def aperturaIndex():
    return render_template('apertura-index.html') 