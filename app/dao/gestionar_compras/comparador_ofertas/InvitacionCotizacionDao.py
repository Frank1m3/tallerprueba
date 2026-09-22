import hashlib
import secrets
from datetime import date, datetime, timedelta
from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

# Estado que ve el usuario: la invitación vence sola al pasar la fecha límite sin respuesta
ESTADO_EFECTIVO = """CASE WHEN i.estado = 'CANCELADA' THEN 'CANCELADA'
                          WHEN i.estado = 'RESPONDIDA' THEN 'RESPONDIDA'
                          WHEN i.fecha_limite < CURRENT_DATE THEN 'VENCIDA'
                          ELSE 'ENVIADA' END"""


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _token_nuevo():
    token = secrets.token_urlsafe(32)          # 256 bits: imposible de adivinar
    return token, _hash(token)


class InvitacionCotizacionDao:

    # ------------------------------------------------------------------
    # Lado interno (usuarios del sistema)
    # ------------------------------------------------------------------
    def proveedores_invitables(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT id_proveedor, prov_nombre, prov_email FROM proveedor ORDER BY prov_nombre")
            return [{"id_proveedor": r[0], "nombre": r[1], "email": r[2]} for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def _solicitud_aprobada(self, cur, nro_solicitud):
        cur.execute("""SELECT id_solicitud, nro_solicitud, estado::text, fecha_necesaria, sucursal
                       FROM v_com_solicitud WHERE nro_solicitud = %s""", (nro_solicitud,))
        s = cur.fetchone()
        if not s or s[2] != 'APROBADA':
            return None
        return {"id_solicitud": s[0], "nro_solicitud": s[1], "fecha_necesaria": s[3], "sucursal": s[4] or ''}

    def items_solicitud(self, cur, id_solicitud):
        cur.execute("""SELECT i.item_code, i.descripcion, sd.cantidad
                       FROM solicitud_compra_det sd JOIN item i ON i.id_item = sd.id_item
                       WHERE sd.id_solicitud = %s ORDER BY i.descripcion""", (id_solicitud,))
        return [{"item_code": r[0], "descripcion": r[1], "cantidad": float(r[2])} for r in cur.fetchall()]

    def crear(self, nro_solicitud, ids_proveedor, fecha_limite, mensaje, enviada_por, fun_id):
        """Crea una invitación por proveedor. Devuelve (solicitud, resultados): cada resultado trae
        el token en claro (solo existe en este momento) o el motivo por el que no se pudo crear."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            sol = self._solicitud_aprobada(cur, nro_solicitud)
            if not sol:
                return None, []
            sol["items"] = self.items_solicitud(cur, sol["id_solicitud"])
            resultados = []
            for id_prov in ids_proveedor:
                cur.execute("SELECT prov_nombre, prov_email FROM proveedor WHERE id_proveedor = %s", (id_prov,))
                p = cur.fetchone()
                if not p:
                    resultados.append({"id_proveedor": id_prov, "proveedor": '?', "error": "El proveedor no existe."})
                    continue
                res = {"id_proveedor": id_prov, "proveedor": p[0], "email": p[1]}
                cur.execute("""SELECT 1 FROM cotizacion_invitacion
                               WHERE id_solicitud = %s AND id_proveedor = %s AND estado <> 'CANCELADA'""",
                            (sol["id_solicitud"], id_prov))
                if cur.fetchone():
                    res["error"] = "Ya tiene una invitación vigente para esta solicitud (usá «Reenviar»)."
                    resultados.append(res); continue
                cur.execute("""SELECT 1 FROM presupuesto_compra_cab
                               WHERE id_solicitud = %s AND id_proveedor = %s AND estado <> 'ANULADO'""",
                            (sol["id_solicitud"], id_prov))
                if cur.fetchone():
                    res["error"] = "Este proveedor ya cotizó esta solicitud."
                    resultados.append(res); continue
                token, token_hash = _token_nuevo()
                cur.execute("""INSERT INTO cotizacion_invitacion
                               (id_solicitud, id_proveedor, token_hash, email_destino, mensaje, fecha_limite, enviada_por, fun_id)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_invitacion""",
                            (sol["id_solicitud"], id_prov, token_hash, p[1], mensaje or None, fecha_limite, enviada_por, fun_id))
                res["id_invitacion"] = cur.fetchone()[0]
                res["token"] = token
                resultados.append(res)
            con.commit()
            return sol, resultados
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al crear invitaciones: {e}")
            return None, []
        finally:
            cur.close(); con.close()

    def listar(self, nro_solicitud):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(f"""
                SELECT i.id_invitacion, i.id_proveedor, p.prov_nombre, i.email_destino, {ESTADO_EFECTIVO},
                       i.fecha_limite, i.fecha_envio, i.fecha_respuesta, i.id_pre_compra_cab, pc.estado, i.observaciones
                FROM cotizacion_invitacion i
                JOIN solicitud_compra_cab sc ON sc.id_solicitud = i.id_solicitud
                JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                LEFT JOIN presupuesto_compra_cab pc ON pc.id_pre_compra_cab = i.id_pre_compra_cab
                WHERE sc.nro_solicitud = %s AND i.estado <> 'CANCELADA'
                ORDER BY i.id_invitacion
            """, (nro_solicitud,))
            return [{
                "id_invitacion": r[0], "id_proveedor": r[1], "proveedor": r[2], "email": r[3], "estado": r[4],
                "fecha_limite": r[5].strftime("%Y-%m-%d"),
                "fecha_envio": r[6].strftime("%Y-%m-%d %H:%M"),
                "fecha_respuesta": r[7].strftime("%Y-%m-%d %H:%M") if r[7] else None,
                "id_presupuesto": r[8], "estado_presupuesto": r[9], "observaciones": r[10] or ''
            } for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def cancelar(self, id_invitacion):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT estado FROM cotizacion_invitacion WHERE id_invitacion = %s", (id_invitacion,))
            f = cur.fetchone()
            if not f:
                return False, 'La invitación no existe.'
            if f[0] == 'RESPONDIDA':
                return False, 'El proveedor ya respondió: anulá su presupuesto desde Presupuesto si no lo querés usar.'
            cur.execute("UPDATE cotizacion_invitacion SET estado = 'CANCELADA' WHERE id_invitacion = %s", (id_invitacion,))
            con.commit()
            return True, None
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al cancelar invitación: {e}")
            return False, 'No se pudo cancelar la invitación.'
        finally:
            cur.close(); con.close()

    def reenviar(self, id_invitacion, fecha_limite):
        """Genera un enlace NUEVO (el anterior deja de funcionar) y extiende la fecha límite."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""SELECT i.estado, i.id_pre_compra_cab, pc.estado, i.id_solicitud, sc.nro_solicitud,
                                  p.prov_nombre, p.prov_email, i.mensaje
                           FROM cotizacion_invitacion i
                           JOIN solicitud_compra_cab sc ON sc.id_solicitud = i.id_solicitud
                           JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                           LEFT JOIN presupuesto_compra_cab pc ON pc.id_pre_compra_cab = i.id_pre_compra_cab
                           WHERE i.id_invitacion = %s""", (id_invitacion,))
            f = cur.fetchone()
            if not f:
                return None, 'La invitación no existe.'
            if f[0] == 'CANCELADA':
                return None, 'La invitación fue cancelada.'
            if f[1] and f[2] != 'PENDIENTE':
                return None, 'La cotización de este proveedor ya fue evaluada.'
            sol = self._solicitud_aprobada(cur, f[4])
            if not sol:
                return None, 'La solicitud ya no está aprobada.'
            sol["items"] = self.items_solicitud(cur, sol["id_solicitud"])
            token, token_hash = _token_nuevo()
            cur.execute("""UPDATE cotizacion_invitacion SET token_hash = %s, fecha_limite = %s, fecha_envio = now()
                           WHERE id_invitacion = %s""", (token_hash, fecha_limite, id_invitacion))
            con.commit()
            return {"id_invitacion": id_invitacion, "proveedor": f[5], "email": f[6], "mensaje": f[7],
                    "token": token, "solicitud": sol}, None
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al reenviar invitación: {e}")
            return None, 'No se pudo reenviar la invitación.'
        finally:
            cur.close(); con.close()

    # ------------------------------------------------------------------
    # Lado del proveedor (portal público, se accede solo con el token)
    # ------------------------------------------------------------------
    def por_token(self, token):
        """Devuelve lo que puede ver el proveedor (solo su invitación) o None si el enlace no existe."""
        if not token or len(token) > 100:
            return None
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(f"""
                SELECT i.id_invitacion, i.id_solicitud, i.id_proveedor, p.prov_nombre, i.mensaje, i.fecha_limite,
                       {ESTADO_EFECTIVO}, i.id_pre_compra_cab, pc.estado, pc.fecha_vencimiento, i.observaciones,
                       i.fecha_respuesta, sc.nro_solicitud, sc.estado::text, sc.fecha_necesaria, sc.sucursal
                FROM cotizacion_invitacion i
                JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                JOIN v_com_solicitud sc ON sc.id_solicitud = i.id_solicitud
                LEFT JOIN presupuesto_compra_cab pc ON pc.id_pre_compra_cab = i.id_pre_compra_cab
                WHERE i.token_hash = %s
            """, (_hash(token),))
            r = cur.fetchone()
            if not r:
                return None
            if r[6] == 'CANCELADA':
                estado = 'CANCELADA'
            elif r[13] != 'APROBADA':
                estado = 'CANCELADA'                        # la solicitud ya no está vigente
            elif r[7] and r[8] != 'PENDIENTE':
                estado = 'EVALUADA'                         # el comprador ya evaluó esa cotización
            elif r[5] < date.today():                       # pasó la fecha límite (aunque ya haya respondido)
                estado = 'VENCIDA'
            else:
                estado = 'ABIERTA'
            items = self.items_solicitud(cur, r[1])
            precios = {}
            if r[7]:
                cur.execute("SELECT item_code, precio_unitario FROM presupuesto_compra_det WHERE id_pre_compra_cab = %s", (r[7],))
                precios = {str(c): float(pr) for c, pr in cur.fetchall()}
            return {
                "id_invitacion": r[0], "id_proveedor": r[2], "proveedor": r[3], "mensaje": r[4],
                "fecha_limite": r[5].strftime("%Y-%m-%d"), "portal_estado": estado,
                "fecha_validez": r[9].strftime("%Y-%m-%d") if r[9] else None,
                "observaciones": r[10] or '', "fecha_respuesta": r[11].strftime("%d/%m/%Y %H:%M") if r[11] else None,
                "solicitud": {"nro": r[12], "fecha_necesaria": r[14].strftime("%d/%m/%Y") if r[14] else None, "sucursal": r[15] or ''},
                "productos": items, "precios": precios
            }
        finally:
            cur.close(); con.close()

    def guardar_cotizacion(self, token, precios, fecha_validez, observaciones, ip):
        """Registra (o actualiza) la cotización del proveedor. Devuelve (ok, mensaje)."""
        datos = self.por_token(token)
        if not datos:
            return False, 'El enlace no es válido.'
        if datos["portal_estado"] != 'ABIERTA':
            return False, 'Este enlace ya no admite cambios.'

        items = {it["item_code"]: it for it in datos["productos"]}
        limpios = {}
        for codigo, valor in (precios or {}).items():
            if codigo not in items:
                return False, 'Hay productos que no pertenecen a la solicitud.'
            if valor in (None, ''):
                continue
            try:
                v = float(valor)
            except (TypeError, ValueError):
                return False, 'Hay precios con formato inválido.'
            if v < 0 or v > 1e11:
                return False, 'Hay precios fuera de rango.'
            if v > 0:
                limpios[codigo] = round(v, 2)
        if not limpios:
            return False, 'Ingresá el precio de al menos un producto.'
        try:
            validez = datetime.strptime(fecha_validez, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return False, 'Indicá hasta cuándo es válida tu oferta.'
        if validez < date.today() or validez > date.today() + timedelta(days=365):
            return False, 'La fecha de validez de la oferta no es correcta.'
        observaciones = (observaciones or '').strip()[:500]

        con = Conexion().getConexion(); cur = con.cursor()
        try:
            # las altas/cambios quedan auditados a nombre del proveedor
            cur.execute("SELECT set_config('myapp.usuario_actual', %s, false)", (('portal:' + datos["proveedor"])[:95],))
            cur.execute("""SELECT id_solicitud, fun_id, id_pre_compra_cab FROM cotizacion_invitacion
                           WHERE id_invitacion = %s FOR UPDATE""", (datos["id_invitacion"],))
            id_solicitud, fun_id, id_pre = cur.fetchone()

            if id_pre:
                cur.execute("UPDATE presupuesto_compra_cab SET fecha_vencimiento = %s WHERE id_pre_compra_cab = %s", (validez, id_pre))
                cur.execute("DELETE FROM presupuesto_compra_det WHERE id_pre_compra_cab = %s", (id_pre,))
            else:
                cur.execute("SELECT COALESCE(MAX(id_pre_compra_cab), 0) + 1 FROM presupuesto_compra_cab")
                cod = str(cur.fetchone()[0])
                cur.execute("""INSERT INTO presupuesto_compra_cab
                               (cod_presupuesto, fun_id, id_proveedor, fecha_emision, fecha_vencimiento, estado, id_solicitud)
                               VALUES (%s, %s, %s, %s, %s, 'PENDIENTE', %s) RETURNING id_pre_compra_cab""",
                            (cod, fun_id, datos["id_proveedor"], date.today(), validez, id_solicitud))
                id_pre = cur.fetchone()[0]
            for codigo, precio in limpios.items():
                cur.execute("""INSERT INTO presupuesto_compra_det (id_pre_compra_cab, item_code, cantidad, precio_unitario)
                               VALUES (%s, %s, %s, %s)""", (id_pre, codigo, items[codigo]["cantidad"], precio))
            cur.execute("""UPDATE cotizacion_invitacion
                           SET estado = 'RESPONDIDA', id_pre_compra_cab = %s, observaciones = %s,
                               fecha_respuesta = now(), ip_respuesta = %s
                           WHERE id_invitacion = %s""", (id_pre, observaciones or None, (ip or '')[:64], datos["id_invitacion"]))
            con.commit()
            return True, None
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al guardar cotización del portal: {e}")
            return False, 'No se pudo registrar la cotización. Intentá nuevamente.'
        finally:
            cur.close(); con.close()
