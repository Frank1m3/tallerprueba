import os
from datetime import date, datetime, timedelta
from html import escape
from flask import Blueprint, jsonify, request, session, current_app as app
from app import csrf
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.comparador_ofertas.ComparadorOfertasDao import ComparadorOfertasDao
from app.dao.gestionar_compras.comparador_ofertas.InvitacionCotizacionDao import InvitacionCotizacionDao
from app.utils.email_sender import enviar_correo_html

cmpapi = Blueprint('cmpapi', __name__)


@cmpapi.route('/solicitudes', methods=['GET'])
def solicitudes():
    return jsonify({'success': True, 'data': ComparadorOfertasDao().solicitudes_con_cotizaciones()})


@cmpapi.route('/solicitud/<int:nro_solicitud>', methods=['GET'])
def comparar(nro_solicitud):
    datos = ComparadorOfertasDao().comparar(nro_solicitud)
    if datos is None:
        return jsonify({'success': False, 'error': 'La solicitud no existe.'}), 404
    return jsonify({'success': True, 'data': datos})


@cmpapi.route('/seleccionar/<int:id_presupuesto>', methods=['PUT'])
@csrf.exempt
def seleccionar(id_presupuesto):
    try:
        ok, error = ComparadorOfertasDao().seleccionar(id_presupuesto)
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': error}), 400
    except Exception as e:
        app.logger.error(f"Error al seleccionar oferta {id_presupuesto}: {e}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500


# =================================
# Portal del proveedor: invitaciones a cotizar
# =================================
def _url_base():
    """URL con la que el proveedor entra al portal. En producción se define PORTAL_URL_BASE en el .env
    (por ejemplo https://compras.granvia.com.py); si no, se usa la dirección desde la que se está trabajando."""
    return (os.environ.get('PORTAL_URL_BASE') or request.host_url).rstrip('/')


def _fun_id_actual():
    con = Conexion().getConexion(); cur = con.cursor()
    try:
        cur.execute("SELECT fun_id FROM usuarios WHERE usu_id = %s", (session.get('usu_id'),))
        f = cur.fetchone()
        return f[0] if f else None
    finally:
        cur.close(); con.close()


def _fecha(valor, por_defecto):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return por_defecto


def _correo(proveedor, solicitud, link, fecha_limite, mensaje):
    """Devuelve (asunto, texto, html) de la invitación."""
    filas = "".join(f"<tr><td style='padding:4px 10px;border-bottom:1px solid #eee'>{escape(it['descripcion'])}</td>"
                    f"<td style='padding:4px 10px;border-bottom:1px solid #eee;text-align:right'>{it['cantidad']:g}</td></tr>"
                    for it in solicitud["items"])
    necesaria = solicitud["fecha_necesaria"].strftime("%d/%m/%Y") if solicitud.get("fecha_necesaria") else "a coordinar"
    limite = fecha_limite.strftime("%d/%m/%Y")
    asunto = "Solicitud de cotización — Gran Vía Supermercados"
    nota = f"<p style='background:#f8fafc;padding:10px;border-radius:6px'>{escape(mensaje)}</p>" if mensaje else ""
    html = f"""<div style="font-family:Arial,sans-serif;max-width:560px;color:#1f2937">
      <h2 style="color:#1e40af">Solicitud de cotización</h2>
      <p>Estimados <b>{escape(proveedor)}</b>: les solicitamos su mejor precio para los siguientes productos.
         Pueden cargarlo ingresando al siguiente enlace.</p>
      {nota}
      <table style="border-collapse:collapse;width:100%;font-size:14px"><tr style="background:#f1f5f9">
        <th style="text-align:left;padding:6px 10px">Producto</th><th style="text-align:right;padding:6px 10px">Cantidad</th></tr>{filas}</table>
      <p>Necesitamos la mercadería para el <b>{necesaria}</b>. Fecha límite para cotizar: <b>{limite}</b>.</p>
      <p style="text-align:center;margin:24px 0"><a href="{link}" style="background:#2563eb;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:bold">Cargar mi cotización</a></p>
      <p style="font-size:12px;color:#6b7280">Si el botón no funciona, copien este enlace en el navegador:<br>{link}<br>
      El enlace es personal: no lo compartan.</p></div>"""
    texto = ("Solicitud de cotización - Gran Vía Supermercados\n\n"
             f"Estimados {proveedor}: les solicitamos su mejor precio para {len(solicitud['items'])} producto(s).\n"
             + (f"{mensaje}\n" if mensaje else "")
             + f"Necesitamos la mercadería para el {necesaria}. Fecha límite para cotizar: {limite}.\n\n"
             f"Carguen su cotización aquí (enlace personal, no lo compartan):\n{link}\n")
    return asunto, texto, html


@cmpapi.route('/proveedores-invitables', methods=['GET'])
def proveedores_invitables():
    return jsonify({'success': True, 'data': InvitacionCotizacionDao().proveedores_invitables()})


@cmpapi.route('/invitaciones/<int:nro_solicitud>', methods=['GET'])
def invitaciones(nro_solicitud):
    return jsonify({'success': True, 'data': InvitacionCotizacionDao().listar(nro_solicitud)})


@cmpapi.route('/invitaciones', methods=['POST'])
@csrf.exempt
def invitar():
    try:
        d = request.get_json(silent=True) or {}
        ids = [int(i) for i in (d.get('proveedores') or [])]
        if not ids:
            return jsonify({'success': False, 'error': 'Elegí al menos un proveedor.'}), 400
        fecha_limite = _fecha(d.get('fecha_limite'), None)
        if not fecha_limite or fecha_limite < date.today():
            return jsonify({'success': False, 'error': 'La fecha límite no puede ser anterior a hoy.'}), 400
        mensaje = (d.get('mensaje') or '').strip()[:500]

        dao = InvitacionCotizacionDao()
        sol, resultados = dao.crear(int(d.get('nro_solicitud') or 0), ids, fecha_limite, mensaje,
                                    session.get('usuario_nombre'), _fun_id_actual())
        if sol is None:
            return jsonify({'success': False, 'error': 'La solicitud no existe.'}), 404

        base = _url_base()
        for r in resultados:
            if r.get('token'):
                r['link'] = f"{base}/cotizar/{r.pop('token')}"
                r['enviado'] = False
                if d.get('enviar_correo') and r.get('email'):
                    asunto, texto, html = _correo(r['proveedor'], sol, r['link'], fecha_limite, mensaje)
                    r['enviado'] = enviar_correo_html(r['email'], asunto, texto, html)
        return jsonify({'success': True, 'data': resultados})
    except Exception as e:
        app.logger.error(f"Error al invitar proveedores: {e}")
        return jsonify({'success': False, 'error': 'Ocurrió un error interno.'}), 500


@cmpapi.route('/invitaciones/<int:id_invitacion>/reenviar', methods=['PUT'])
@csrf.exempt
def reenviar(id_invitacion):
    d = request.get_json(silent=True) or {}
    fecha_limite = _fecha(d.get('fecha_limite'), date.today() + timedelta(days=5))
    if fecha_limite < date.today():
        return jsonify({'success': False, 'error': 'La fecha límite no puede ser anterior a hoy.'}), 400
    inv, error = InvitacionCotizacionDao().reenviar(id_invitacion, fecha_limite)
    if error:
        return jsonify({'success': False, 'error': error}), 400
    link = f"{_url_base()}/cotizar/{inv['token']}"
    enviado = False
    if d.get('enviar_correo') and inv.get('email'):
        asunto, texto, html = _correo(inv['proveedor'], inv['solicitud'], link, fecha_limite, inv.get('mensaje'))
        enviado = enviar_correo_html(inv['email'], asunto, texto, html)
    return jsonify({'success': True, 'data': {'proveedor': inv['proveedor'], 'email': inv['email'], 'link': link, 'enviado': enviado}})


@cmpapi.route('/invitaciones/<int:id_invitacion>/cancelar', methods=['PUT'])
@csrf.exempt
def cancelar(id_invitacion):
    ok, error = InvitacionCotizacionDao().cancelar(id_invitacion)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': error}), 400
