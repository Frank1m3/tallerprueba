from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class TipoItemDao:

    def getAll(self):
        sql = "SELECT id_tipo_item, descripcion FROM tipo_item ORDER BY descripcion"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll tipo_item: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getById(self, id):
        sql = "SELECT id_tipo_item, descripcion FROM tipo_item WHERE id_tipo_item = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id,))
            r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById tipo_item: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardar(self, descripcion):
        sql = "INSERT INTO tipo_item (descripcion) VALUES (%s) RETURNING id_tipo_item"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,))
            id_inserted = cur.fetchone()[0]
            con.commit()
            return id_inserted
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar tipo_item: {e}")
            con.rollback()
            return None
        finally:
            cur.close()
            con.close()

    def update(self, id, descripcion):
        sql = "UPDATE tipo_item SET descripcion = %s WHERE id_tipo_item = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id))
            con.commit()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update tipo_item: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def delete(self, id):
        sql = "DELETE FROM tipo_item WHERE id_tipo_item = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id,))
            con.commit()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete tipo_item: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()
