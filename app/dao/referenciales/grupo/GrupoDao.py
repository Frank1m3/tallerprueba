from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class GrupoDao:

    def getAll(self):
        sql = "SELECT gru_id, gru_des FROM grupos ORDER BY gru_des"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll grupos: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT gru_id, gru_des FROM grupos WHERE gru_id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById grupos: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, descripcion):
        sql = "INSERT INTO grupos (gru_des) VALUES (%s) RETURNING gru_id"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar grupos: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, descripcion):
        sql = "UPDATE grupos SET gru_des = %s WHERE gru_id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update grupos: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM grupos WHERE gru_id = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete grupos: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
