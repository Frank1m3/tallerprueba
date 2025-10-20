import os
import time
import json
from flask import Blueprint, render_template, request, jsonify, current_app

from app.dao.referenciales.sucursal.sucursal_dao import SucursalDao
from app.dao.referenciales.funcionario.funcionario_dao import FuncionarioDao
from app.dao.gestionar_compras.registrar_presupuesto.PresupuestoDao import PresupuestoCompraDao
from app.dao.gestionar_compras.registrar_pedido_compras.pedido_de_compras_dao import PedidoDeComprasDao

presumod = Blueprint('presumod', __name__, template_folder='templates')

# ================================
# Tipos de archivos permitidos
# ================================
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'txt'}

def archivo_permitido(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    folder = os.path.join(current_app.root_path, 'static', 'presupuestos')
    os.makedirs(folder, exist_ok=True)
    return folder

# ================================
# Index de presupuestos
# ================================
@presumod.route('/presupuesto-index')
def presupuesto_index():
    dao = PresupuestoCompraDao()
    presupuestos = dao.listar()
    return render_template('presupuesto_index.html', presupuestos=presupuestos)

# ================================
# Agregar presupuesto
# ================================
@presumod.route('/presupuesto-agregar')
def presupuesto_agregar():
    pdao = PedidoDeComprasDao()
    sdao = SucursalDao()
    fdao = FuncionarioDao()

    productos = pdao.obtener_productos()
    proveedores_dict = {p['id_proveedor']: p['proveedor_nombre'] for p in productos if p['id_proveedor']}
    proveedores = [{'id_proveedor': k, 'nombre_proveedor': v} for k, v in proveedores_dict.items()]

    return render_template(
        'presupuesto_agregar.html',
        proveedores=proveedores,
        sucursales=sdao.getSucursales(),
        funcionarios=fdao.get_funcionarios(),
        mercaderias=productos
    )

# ================================
# Subir archivo AJAX
# ================================
@presumod.route('/subir-archivo', methods=['POST'])
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
        ruta_relativa = os.path.join('presupuestos', nombre_archivo)
        return jsonify({'success': True, 'nombre': nombre_archivo, 'ruta': ruta_relativa})
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo: {e}")
        return jsonify({'success': False, 'error': f'Error guardando archivo: {str(e)}'})

# ================================
# Guardar presupuesto completo
# ================================
@presumod.route('/guardar-presupuesto', methods=['POST'])
def guardar_presupuesto():
    try:
        cod_presupuesto = request.form.get('cod_presupuesto')
        fecha_emision = request.form.get('fecha_emision')
        fecha_vencimiento = request.form.get('fecha_vencimiento')
        id_proveedor = int(request.form.get('id_proveedor') or 0)
        fun_id = int(request.form.get('fun_id') or 0)
        estado = request.form.get('estado', 'PENDIENTE')
        detalles_raw = request.form.get('detalles', '[]')

        try:
            detalles_list = json.loads(detalles_raw)
        except Exception:
            detalles_list = []

        from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_dto import PresupuestoCompraDto
        from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_detalle_dto import PresupuestoCompraDetalleDto
        dao = PresupuestoCompraDao()

        detalles_dto = [
            PresupuestoCompraDetalleDto(
                item_code=d['item_code'],
                cantidad=d['cantidad'],
                precio_unitario=d['precio_unitario']
            ) for d in detalles_list
        ]

        # Archivo opcional enviado en el mismo formulario
        archivo = request.files.get('archivo')
        ruta_relativa = None
        if archivo and archivo.filename:
            if not archivo_permitido(archivo.filename):
                return jsonify({'success': False, 'error': 'Tipo de archivo no permitido'})
            nombre_archivo = f"{int(time.time())}_{archivo.filename}"
            ruta_absoluta = os.path.join(get_upload_folder(), nombre_archivo)
            archivo.save(ruta_absoluta)
            ruta_relativa = os.path.join('presupuestos', nombre_archivo)

        dto = PresupuestoCompraDto(
            cod_presupuesto=cod_presupuesto,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            id_proveedor=id_proveedor,
            fun_id=fun_id,
            condicion_compra='',
            estado=estado,
            archivo=ruta_relativa,
            detalles=detalles_dto
        )

        success = dao.insertar(dto)
        return jsonify({'success': success})

    except Exception as e:
        current_app.logger.error(f"Error guardando presupuesto: {e}")
        return jsonify({'success': False, 'error': str(e)})
