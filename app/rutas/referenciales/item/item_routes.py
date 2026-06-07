from flask import Blueprint, render_template

item_mod = Blueprint('item', __name__, template_folder='templates')

@item_mod.route('/item')
def itemIndex():
    return render_template('item-index.html')
