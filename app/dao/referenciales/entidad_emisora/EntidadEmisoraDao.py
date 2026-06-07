from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class EntidadEmisoraDao:

    def getAll(self):
        sql = "SELECT id_entidad_emisora, descripcion FROM entidad_emisora ORDER BY descripcion"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll entidad_emisora: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT id_entidad_emisora, descripcion FROM entidad_emisora WHERE id_entidad_emisora = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById entidad_emisora: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, descripcion):
        sql = "INSERT INTO entidad_emisora (descripcion) VALUES (%s) RETURNING id_entidad_emisora"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar entidad_emisora: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, descripcion):
        sql = "UPDATE entidad_emisora SET descripcion = %s WHERE id_entidad_emisora = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update entidad_emisora: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM entidad_emisora WHERE id_entidad_emisora = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete entidad_emisora: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
