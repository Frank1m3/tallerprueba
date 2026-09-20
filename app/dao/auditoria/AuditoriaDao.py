from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2
import json


class AuditoriaDao:

    def listar(self, tabla=None, usuario=None, operacion=None, desde=None, hasta=None,
               limit=15, offset=0, q=None):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            condiciones = ["1=1"]
            params = {"limit": limit, "offset": offset}
            if tabla:
                condiciones.append("tabla = %(tabla)s"); params["tabla"] = tabla
            if usuario:
                condiciones.append("usuario ILIKE %(usuario)s"); params["usuario"] = f"%{usuario}%"
            if operacion:
                condiciones.append("operacion = %(operacion)s"); params["operacion"] = operacion
            if desde:
                condiciones.append("fecha_hora >= %(desde)s"); params["desde"] = desde
            if hasta:
                condiciones.append("fecha_hora < (%(hasta)s::date + interval '1 day')"); params["hasta"] = hasta
            if q:
                condiciones.append("(datos_nuevos::text ILIKE %(q)s OR datos_anteriores::text ILIKE %(q)s)")
                params["q"] = f"%{q}%"
            where_sql = " AND ".join(condiciones)

            sql = f"""
                SELECT id_auditoria, tabla, operacion, usuario, fecha_hora, resultado,
                       datos_anteriores, datos_nuevos, COUNT(*) OVER() AS total_filas
                FROM auditoria
                WHERE {where_sql}
                ORDER BY id_auditoria DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            cur.execute(sql, params)
            filas = cur.fetchall()
            total = filas[0][8] if filas else 0
            return [{
                "id_auditoria": r[0], "tabla": r[1], "operacion": r[2], "usuario": r[3],
                "fecha_hora": r[4].strftime('%Y-%m-%d %H:%M:%S') if r[4] else None,
                "resultado": r[5],
                "datos_anteriores": r[6], "datos_nuevos": r[7]
            } for r in filas], total
        except psycopg2.Error as e:
            app.logger.error(f"Error en AuditoriaDao.listar: {e}")
            return [], 0
        finally:
            cur.close(); con.close()

    def tablas_auditadas(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT DISTINCT tabla FROM auditoria ORDER BY tabla")
            return [r[0] for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en tablas_auditadas: {e}")
            return []
        finally:
            cur.close(); con.close()

    def resumen(self, desde=None, hasta=None):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            condiciones = ["1=1"]
            params = {}
            if desde:
                condiciones.append("fecha_hora >= %(desde)s"); params["desde"] = desde
            if hasta:
                condiciones.append("fecha_hora < (%(hasta)s::date + interval '1 day')"); params["hasta"] = hasta
            where_sql = " AND ".join(condiciones)
            cur.execute(f"""
                SELECT operacion, COUNT(*) FROM auditoria WHERE {where_sql} GROUP BY operacion
            """, params)
            por_operacion = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute(f"""
                SELECT tabla, COUNT(*) FROM auditoria WHERE {where_sql}
                GROUP BY tabla ORDER BY COUNT(*) DESC LIMIT 5
            """, params)
            top_tablas = [{"tabla": r[0], "cantidad": r[1]} for r in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM auditoria WHERE {where_sql}", params)
            total = cur.fetchone()[0]
            return {"total": total, "por_operacion": por_operacion, "top_tablas": top_tablas}
        except psycopg2.Error as e:
            app.logger.error(f"Error en resumen auditoria: {e}")
            return {"total": 0, "por_operacion": {}, "top_tablas": []}
        finally:
            cur.close(); con.close()
