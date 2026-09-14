import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app

from app.dao.gestionar_compras.registrar_factura_compras.FacturaCompraDao import FacturaCompraDao

facmod = Blueprint('facmod', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'txt'}

def archivo_permitido(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    folder = os.path.join(current_app.root_path, 'static', 'facturas')
    os.makedirs(folder, exist_ok=True)
    return folder


@facmod.route('/facturas-index')
def facturas_index():
    return render_template('factura_index.html')


@facmod.route('/factura-agregar')
def factura_agregar():
    from app.dao.referenciales.item.ItemDao import ItemDao
    dao = FacturaCompraDao()
    recepciones = dao.obtener_recepciones_disponibles()
    tipos_impuesto = ItemDao().getCombos().get('impuestos', [])
    return render_template('factura_agregar.html', recepciones=recepciones, tipos_impuesto=tipos_impuesto)


@facmod.route('/subir-archivo', methods=['POST'])
def subir_archivo():
    archivo = request.files.get('archivo')
    if not archivo or archivo.filename == '':
        return jsonify({'success': False, 'error': 'No se recibió archivo o nombre vacío'})

    if not archivo_permitido(archivo.filename):
        return jsonify({'success': False, 'error': 'Tipo de archivo no permitido'})

    nombre_archivo = f"{int(time.time())}_{archivo.filename}"
    ruta_absoluta = os.path.join(get_upload_folder(), nombre_archivo)

    try:
        archivo.save(ruta_absoluta)
        ruta_relativa = os.path.join('facturas', nombre_archivo)
        return jsonify({'success': True, 'nombre': nombre_archivo, 'ruta': ruta_relativa})
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo: {e}")
        return jsonify({'success': False, 'error': f'Error guardando archivo: {str(e)}'})
