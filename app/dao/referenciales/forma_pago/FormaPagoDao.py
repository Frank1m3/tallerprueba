from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class FormaPagoDao:

    def getFormasPago(self):
        sql = "SELECT id, descripcion FROM formas_pago ORDER BY descripcion"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            resultados = cur.fetchall()
            return [{"id": r[0], "descripcion": r[1]} for r in resultados]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getFormasPago: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getFormaPagoById(self, id):
        sql = "SELECT id, descripcion FROM formas_pago WHERE id = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id,))
            r = cur.fetchone()
            if r:
                return {"id": r[0], "descripcion": r[1]}
            return None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getFormaPagoById: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardarFormaPago(self, descripcion):
        sql = "INSERT INTO formas_pago (descripcion) VALUES (%s) RETURNING id"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion,))
            id_inserted = cur.fetchone()[0]
            con.commit()
            return id_inserted
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardarFormaPago: {e}")
            con.rollback()
            return None
        finally:
            cur.close()
            con.close()

    def updateFormaPago(self, id, descripcion):
        sql = "UPDATE formas_pago SET descripcion = %s WHERE id = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id))
            con.commit()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en updateFormaPago: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def deleteFormaPago(self, id):
        sql = "DELETE FROM formas_pago WHERE id = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id,))
            con.commit()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en deleteFormaPago: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()
