from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class MotivoAjusteDao:

    def getAll(self):
        sql = "SELECT id_motivo_ajuste, descripcion FROM motivo_ajuste ORDER BY descripcion"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll motivo_ajuste: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT id_motivo_ajuste, descripcion FROM motivo_ajuste WHERE id_motivo_ajuste = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById motivo_ajuste: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, descripcion):
        sql = "INSERT INTO motivo_ajuste (descripcion) VALUES (%s) RETURNING id_motivo_ajuste"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar motivo_ajuste: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, descripcion):
        sql = "UPDATE motivo_ajuste SET descripcion = %s WHERE id_motivo_ajuste = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update motivo_ajuste: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM motivo_ajuste WHERE id_motivo_ajuste = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete motivo_ajuste: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
