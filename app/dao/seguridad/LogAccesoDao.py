import threading
from flask import current_app as app, request
from app.conexion.Conexion import Conexion
from app.utils.email_sender import enviar_alerta_acceso
import psycopg2


def _ip_cliente():
    try:
        return request.remote_addr
    except RuntimeError:
        return None


class LogAccesoDao:

    def registrar(self, usuario_intentado, evento, id_usuario=None, detalle=None):
        """Registra un intento de acceso. Nunca interrumpe el login si falla."""
        try:
            ip = _ip_cliente()
            user_agent = request.headers.get('User-Agent', '')[:300] if request else None
        except RuntimeError:
            ip, user_agent = None, None
        try:
            con = Conexion().getConexion(); cur = con.cursor()
            cur.execute("""
                INSERT INTO log_acceso (usuario_intentado, id_usuario, evento, detalle, ip, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ((usuario_intentado or '(vacío)')[:100], id_usuario, evento, detalle, ip, user_agent))
            con.commit()
            cur.close(); con.close()
        except Exception as e:
            app.logger.error(f"No se pudo registrar el intento de acceso: {e}")

    def emails_administradores(self):
        try:
            con = Conexion().getConexion(); cur = con.cursor()
            cur.execute("""
                SELECT DISTINCT u.usu_email FROM usuarios u
                JOIN grupos g ON g.gru_id = u.gru_id
                WHERE g.gru_des = 'administradores' AND u.usu_estado IS TRUE AND u.usu_email IS NOT NULL
            """)
            emails = [r[0] for r in cur.fetchall()]
            cur.close(); con.close()
            return emails
        except Exception as e:
            app.logger.error(f"No se pudieron leer los correos de administradores: {e}")
            return []

    def enviar_alerta_async(self, destinatarios, asunto, cuerpo):
        """Envía la alerta en un hilo aparte para no demorar la respuesta del login."""
        flask_app = app._get_current_object()

        def _enviar():
            with flask_app.app_context():
                enviar_alerta_acceso(destinatarios, asunto, cuerpo)
        threading.Thread(target=_enviar, daemon=True).start()

    def listar(self, desde=None, hasta=None, usuario=None, evento=None, ip=None,
               limit=15, offset=0):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            condiciones = ["1=1"]; params = {"limit": limit, "offset": offset}
            if desde:
                condiciones.append("fecha_hora >= %(desde)s"); params["desde"] = desde
            if hasta:
                condiciones.append("fecha_hora < (%(hasta)s::date + interval '1 day')"); params["hasta"] = hasta
            if usuario:
                condiciones.append("usuario_intentado ILIKE %(usuario)s"); params["usuario"] = f"%{usuario}%"
            if evento:
                condiciones.append("evento = %(evento)s"); params["evento"] = evento
            if ip:
                condiciones.append("ip ILIKE %(ip)s"); params["ip"] = f"%{ip}%"
            cur.execute(f"""
                SELECT id_log, usuario_intentado, evento, detalle, ip, user_agent, fecha_hora,
                       COUNT(*) OVER() AS total
                FROM log_acceso WHERE {' AND '.join(condiciones)}
                ORDER BY id_log DESC LIMIT %(limit)s OFFSET %(offset)s
            """, params)
            filas = cur.fetchall()
            total = filas[0][7] if filas else 0
            return [{
                "id_log": r[0], "usuario": r[1], "evento": r[2], "detalle": r[3], "ip": r[4],
                "user_agent": r[5],
                "fecha_hora": r[6].strftime('%Y-%m-%d %H:%M:%S') if r[6] else None
            } for r in filas], total
        except psycopg2.Error as e:
            app.logger.error(f"Error en LogAccesoDao.listar: {e}")
            return [], 0
        finally:
            cur.close(); con.close()

    def resumen(self, desde=None, hasta=None):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            condiciones = ["1=1"]; params = {}
            if desde:
                condiciones.append("fecha_hora >= %(desde)s"); params["desde"] = desde
            if hasta:
                condiciones.append("fecha_hora < (%(hasta)s::date + interval '1 day')"); params["hasta"] = hasta
            where = " AND ".join(condiciones)
            cur.execute(f"SELECT evento, COUNT(*) FROM log_acceso WHERE {where} GROUP BY evento", params)
            por_evento = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute(f"""
                SELECT ip, COUNT(*) FROM log_acceso
                WHERE {where} AND evento IN ('LOGIN_FALLIDO','USUARIO_INEXISTENTE','2FA_FALLIDO') AND ip IS NOT NULL
                GROUP BY ip HAVING COUNT(*) >= 3 ORDER BY COUNT(*) DESC LIMIT 5
            """, params)
            ips_sospechosas = [{"ip": r[0], "fallos": r[1]} for r in cur.fetchall()]
            return {"por_evento": por_evento, "ips_sospechosas": ips_sospechosas}
        except psycopg2.Error as e:
            app.logger.error(f"Error en LogAccesoDao.resumen: {e}")
            return {"por_evento": {}, "ips_sospechosas": []}
        finally:
            cur.close(); con.close()
