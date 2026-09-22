"""Reglas del ciclo de compras: un documento solo puede usarse en el paso siguiente si está APROBADO.

    Solicitud  (APROBADA) -> Presupuesto y Pedido
    Presupuesto (APROBADO) -> Pedido y Orden de compra
    Pedido     (APROBADO) -> Recepción

Cada función devuelve None si el documento se puede usar (o si no existe: en ese caso
el flujo normal ya responde "no encontrado") y, si no está aprobado, el mismo mensaje que si
no existiera: a propósito no se aclara el motivo.
Se usan tanto al buscar el documento de origen como al grabar, para que la regla no se
pueda saltear llamando directamente a la API.
"""
from app.conexion.Conexion import Conexion


def _fila(sql, params):
    con = Conexion().getConexion(); cur = con.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close(); con.close()


def error_solicitud_no_aprobada(nro=None, id_solicitud=None):
    try:
        if id_solicitud:
            fila = _fila("SELECT estado::text, nro_solicitud FROM solicitud_compra_cab WHERE id_solicitud = %s", (int(id_solicitud),))
        elif nro not in (None, ''):
            fila = _fila("SELECT estado::text, nro_solicitud FROM solicitud_compra_cab WHERE nro_solicitud = %s", (int(nro),))
        else:
            return None
    except (TypeError, ValueError):
        return None
    if not fila or fila[0] == 'APROBADA':
        return None
    return "La solicitud no existe."


def error_presupuesto_no_aprobado(cod=None, id_presupuesto=None):
    if id_presupuesto:
        fila = _fila("SELECT estado, cod_presupuesto FROM presupuesto_compra_cab WHERE id_pre_compra_cab = %s", (int(id_presupuesto),))
    elif cod:
        # mismo criterio que usan las pantallas para resolver el código: el más reciente
        fila = _fila("""SELECT estado, cod_presupuesto FROM presupuesto_compra_cab
                        WHERE cod_presupuesto = %s ORDER BY id_pre_compra_cab DESC LIMIT 1""", (cod,))
    else:
        return None
    if not fila or fila[0] == 'APROBADO':
        return None
    return "El presupuesto no existe."


def error_pedido_no_aprobado(nro=None, id_pedido=None):
    if id_pedido:
        fila = _fila("SELECT estado, nro_pedido FROM pedido_compra_cab WHERE id_pedido_compra_cab = %s", (int(id_pedido),))
    elif nro:
        fila = _fila("SELECT estado, nro_pedido FROM pedido_compra_cab WHERE nro_pedido = %s ORDER BY id_pedido_compra_cab DESC LIMIT 1", (str(nro),))
    else:
        return None
    if not fila or fila[0] == 'APROBADO':
        return None
    return "El pedido no existe."
