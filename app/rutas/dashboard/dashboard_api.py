from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from app.dao.dashboard.DashboardDao import DashboardDao

dashapi = Blueprint('dashapi', __name__)


def _parse_filtros(args):
    hasta = args.get('hasta') or date.today().isoformat()
    desde = args.get('desde') or (date.today() - timedelta(days=90)).isoformat()
    id_sucursal = args.get('id_sucursal', type=int)
    id_deposito = args.get('id_deposito', type=int)
    return desde, hasta, id_sucursal, id_deposito


@dashapi.route('/resumen', methods=['GET'])
def resumen():
    desde, hasta, id_sucursal, id_deposito = _parse_filtros(request.args)
    dias_sin_movimiento = request.args.get('dias_sin_movimiento', 30, type=int)

    data = DashboardDao().obtener_resumen(desde, hasta, id_sucursal, id_deposito, dias_sin_movimiento)
    if data is None:
        return jsonify({"success": False, "error": "No se pudo calcular el resumen del dashboard"}), 500
    data["filtros"] = {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal, "id_deposito": id_deposito}
    return jsonify({"success": True, "data": data})


@dashapi.route('/riesgo-stock', methods=['GET'])
def riesgo_stock_listado():
    desde, hasta, id_sucursal, id_deposito = _parse_filtros(request.args)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 15, type=int)
    draw = request.args.get('draw', 1, type=int)
    q = (request.args.get('search[value]') or '').strip() or None

    filas, total = DashboardDao().riesgo_stock_paginado(desde, hasta, id_sucursal, id_deposito, length, start, q)
    return jsonify({"draw": draw, "recordsTotal": total, "recordsFiltered": total, "data": filas})


@dashapi.route('/sin-stock', methods=['GET'])
def sin_stock_listado():
    _, _, id_sucursal, id_deposito = _parse_filtros(request.args)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 15, type=int)
    draw = request.args.get('draw', 1, type=int)
    q = (request.args.get('search[value]') or '').strip() or None

    filas, total = DashboardDao().sin_stock_paginado(id_sucursal, id_deposito, length, start, q)
    return jsonify({"draw": draw, "recordsTotal": total, "recordsFiltered": total, "data": filas})
