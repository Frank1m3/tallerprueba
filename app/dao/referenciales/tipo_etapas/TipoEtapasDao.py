from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class TipoEtapasDao:

    def getAll(self):
        sql = "SELECT id_etapa, descripcion, tipo_etapa FROM tipo_etapas ORDER BY descripcion"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{"id": r[0], "descripcion": r[1], "tipo_etapa": r[2]} for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll tipo_etapas: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = "SELECT id_etapa, descripcion, tipo_etapa FROM tipo_etapas WHERE id_etapa = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            return {"id": r[0], "descripcion": r[1], "tipo_etapa": r[2]} if r else None
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById tipo_etapas: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, descripcion, tipo_etapa):
        sql = """INSERT INTO tipo_etapas (descripcion, tipo_etapa, fecha_creacion)
                 VALUES (%s, %s, CURRENT_DATE) RETURNING id_etapa"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, tipo_etapa)); idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar tipo_etapas: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, descripcion, tipo_etapa):
        sql = """UPDATE tipo_etapas SET descripcion = %s, tipo_etapa = %s, fecha_modificacion = CURRENT_DATE
                 WHERE id_etapa = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, tipo_etapa, id)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update tipo_etapas: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM tipo_etapas WHERE id_etapa = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete tipo_etapas: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()
