from flask import Blueprint, request, jsonify
from app.dao.auditoria.AuditoriaDao import AuditoriaDao
from app.utilidades.seguridad import admin_required

audapi = Blueprint('audapi', __name__)


@audapi.route('/listado', methods=['GET'])
@admin_required
def listado():
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 15, type=int)
    draw = request.args.get('draw', 1, type=int)
    q = (request.args.get('search[value]') or '').strip() or None

    tabla = request.args.get('tabla') or None
    usuario = request.args.get('usuario') or None
    operacion = request.args.get('operacion') or None
    desde = request.args.get('desde') or None
    hasta = request.args.get('hasta') or None

    filas, total = AuditoriaDao().listar(tabla, usuario, operacion, desde, hasta, length, start, q)
    return jsonify({"draw": draw, "recordsTotal": total, "recordsFiltered": total, "data": filas})


@audapi.route('/resumen', methods=['GET'])
@admin_required
def resumen():
    desde = request.args.get('desde') or None
    hasta = request.args.get('hasta') or None
    return jsonify({"success": True, "data": AuditoriaDao().resumen(desde, hasta)})


@audapi.route('/accesos', methods=['GET'])
@admin_required
def accesos_listado():
    from app.dao.seguridad.LogAccesoDao import LogAccesoDao
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 15, type=int)
    draw = request.args.get('draw', 1, type=int)
    filas, total = LogAccesoDao().listar(
        request.args.get('desde') or None, request.args.get('hasta') or None,
        request.args.get('usuario') or None, request.args.get('evento') or None,
        request.args.get('ip') or None, length, start)
    return jsonify({"draw": draw, "recordsTotal": total, "recordsFiltered": total, "data": filas})


@audapi.route('/accesos/resumen', methods=['GET'])
@admin_required
def accesos_resumen():
    from app.dao.seguridad.LogAccesoDao import LogAccesoDao
    return jsonify({"success": True, "data": LogAccesoDao().resumen(
        request.args.get('desde') or None, request.args.get('hasta') or None)})
