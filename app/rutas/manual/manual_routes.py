import os
from flask import Blueprint, render_template, send_from_directory

manualmod = Blueprint('manualmod', __name__, template_folder='templates')
ARCHIVOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'archivos')

MANUAL_VERSION = '1.1'
MANUAL_FECHA = '20 de septiembre de 2026'


@manualmod.route('/')
def manual_index():
    return render_template('manual.html', version=MANUAL_VERSION, fecha=MANUAL_FECHA)


# Capturas, PDF y texto del manual: se sirven por acá (y no desde /static) para que exijan sesión,
# ya que las imágenes muestran datos internos del sistema.
@manualmod.route('/archivo/<path:ruta>')
def manual_archivo(ruta):
    return send_from_directory(ARCHIVOS, ruta)
