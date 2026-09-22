"""Portal del proveedor: página pública (sin usuario) a la que se entra solo con el enlace personal
/cotizar/<token>. Expone únicamente lo necesario para cotizar una solicitud y nada más del sistema."""
import time
from flask import Blueprint, render_template, request, jsonify
from app.dao.gestionar_compras.comparador_ofertas.InvitacionCotizacionDao import InvitacionCotizacionDao
from app.dao.seguridad.LogAccesoDao import LogAccesoDao

portalmod = Blueprint('portalmod', __name__, template_folder='templates')

# Freno a quien prueba enlaces al azar: 20 enlaces inválidos en 10 minutos desde la misma IP
_FALLOS = {}
_MAX_FALLOS, _VENTANA = 20, 600


def _bloqueada(ip):
    ahora = time.time()
    _FALLOS[ip] = [t for t in _FALLOS.get(ip, []) if ahora - t < _VENTANA]
    return len(_FALLOS[ip]) >= _MAX_FALLOS


def _fallo(ip):
    _FALLOS.setdefault(ip, []).append(time.time())
    LogAccesoDao().registrar('(portal proveedor)', 'PORTAL_TOKEN_INVALIDO', None, 'Enlace de cotización inexistente o inválido')


@portalmod.after_request
def _cabeceras(resp):
    resp.headers['Cache-Control'] = 'no-store'                 # el enlace es personal: nada en caché
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'         # que no lo indexe ningún buscador
    resp.headers['Referrer-Policy'] = 'no-referrer'            # el enlace no viaja a sitios externos
    resp.headers['X-Frame-Options'] = 'DENY'
    return resp


@portalmod.route('/<token>', methods=['GET'])
def portal(token):
    ip = request.remote_addr
    if _bloqueada(ip):
        return render_template('portal_cotizacion.html', datos=None, token=None, bloqueado=True), 429
    datos = InvitacionCotizacionDao().por_token(token)
    if not datos:
        _fallo(ip)
        return render_template('portal_cotizacion.html', datos=None, token=None, bloqueado=False), 404
    return render_template('portal_cotizacion.html', datos=datos, token=token, bloqueado=False)


@portalmod.route('/<token>/enviar', methods=['POST'])
def enviar(token):
    ip = request.remote_addr
    if _bloqueada(ip):
        return jsonify({'success': False, 'error': 'Demasiados intentos. Probá más tarde.'}), 429
    d = request.get_json(silent=True) or {}
    dao = InvitacionCotizacionDao()
    ok, error = dao.guardar_cotizacion(token, d.get('precios'), d.get('fecha_validez'), d.get('observaciones'), ip)
    if not ok:
        return jsonify({'success': False, 'error': error}), 400
    datos = dao.por_token(token) or {}
    LogAccesoDao().registrar(datos.get('proveedor', '(portal proveedor)'), 'PORTAL_COTIZACION_ENVIADA', None,
                             f"Cotización recibida para la solicitud #{(datos.get('solicitud') or {}).get('nro', '?')}")
    return jsonify({'success': True})
