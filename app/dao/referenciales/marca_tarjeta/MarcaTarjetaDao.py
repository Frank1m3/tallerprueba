from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class MarcaTarjetaDao:

    def getAll(self):
        sql = "SELECT id_marca_tarjeta, descripcion FROM marca_tarjeta ORDER BY descripcion"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll marca_tarjeta: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT id_marca_tarjeta, descripcion FROM marca_tarjeta WHERE id_marca_tarjeta = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById marca_tarjeta: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, descripcion):
        sql = "INSERT INTO marca_tarjeta (descripcion) VALUES (%s) RETURNING id_marca_tarjeta"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar marca_tarjeta: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, descripcion):
        sql = "UPDATE marca_tarjeta SET descripcion = %s WHERE id_marca_tarjeta = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update marca_tarjeta: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM marca_tarjeta WHERE id_marca_tarjeta = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete marca_tarjeta: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
