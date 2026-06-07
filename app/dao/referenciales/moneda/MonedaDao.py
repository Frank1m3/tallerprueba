from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class MonedaDao:

    def getAll(self):
        sql = "SELECT id, codigo, descripcion FROM monedas ORDER BY descripcion"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "codigo": r[1], "descripcion": r[2]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll monedas: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT id, codigo, descripcion FROM monedas WHERE id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "codigo": r[1], "descripcion": r[2]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById monedas: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, codigo, descripcion):
        sql = "INSERT INTO monedas (codigo, descripcion) VALUES (%s, %s) RETURNING id"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (codigo, descripcion)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar monedas: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, codigo, descripcion):
        sql = "UPDATE monedas SET codigo = %s, descripcion = %s WHERE id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (codigo, descripcion, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update monedas: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM monedas WHERE id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete monedas: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
