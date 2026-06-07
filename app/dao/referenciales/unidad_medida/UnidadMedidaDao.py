from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class UnidadMedidaDao:

    def getAll(self):
        sql = """SELECT id_unidad_medida, codigo_unidad, descripcion, tipo_unidad
                 FROM unidad_medida ORDER BY descripcion"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "codigo": r[1], "descripcion": r[2], "tipo": r[3]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll unidad_medida: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = """SELECT id_unidad_medida, codigo_unidad, descripcion, tipo_unidad
                 FROM unidad_medida WHERE id_unidad_medida = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "codigo": r[1], "descripcion": r[2], "tipo": r[3]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById unidad_medida: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, codigo, descripcion, tipo):
        sql = """INSERT INTO unidad_medida (codigo_unidad, descripcion, tipo_unidad, fecha_creacion)
                 VALUES (%s, %s, %s, CURRENT_DATE) RETURNING id_unidad_medida"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (codigo, descripcion, tipo)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar unidad_medida: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, codigo, descripcion, tipo):
        sql = """UPDATE unidad_medida
                 SET codigo_unidad = %s, descripcion = %s, tipo_unidad = %s, fecha_modificacion = CURRENT_DATE
                 WHERE id_unidad_medida = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (codigo, descripcion, tipo, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update unidad_medida: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM unidad_medida WHERE id_unidad_medida = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete unidad_medida: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
