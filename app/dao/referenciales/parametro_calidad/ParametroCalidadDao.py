from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class ParametroCalidadDao:

    def getAll(self):
        sql = """
            SELECT p.id_parametro, p.descripcion, p.valor_minimo, p.valor_maximo,
                   p.id_tipo_etapa, te.descripcion AS etapa_desc,
                   p.id_unidad_medida, u.descripcion AS unidad_desc
            FROM parametros_control_calidad p
            LEFT JOIN tipo_etapas te  ON te.id_etapa = p.id_tipo_etapa
            LEFT JOIN unidad_medida u ON u.id_unidad_medida = p.id_unidad_medida
            ORDER BY p.id_parametro
        """
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                "id": r[0], "descripcion": r[1],
                "valor_minimo": float(r[2]) if r[2] is not None else None,
                "valor_maximo": float(r[3]) if r[3] is not None else None,
                "id_tipo_etapa": r[4], "etapa_desc": r[5],
                "id_unidad_medida": r[6], "unidad_desc": r[7]
            } for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getAll parametros: {e}"); return []
        finally:
            cur.close(); con.close()

    def getById(self, id):
        sql = """SELECT id_parametro, descripcion, valor_minimo, valor_maximo,
                        id_tipo_etapa, id_unidad_medida
                 FROM parametros_control_calidad WHERE id_parametro = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            if not r: return None
            return {
                "id": r[0], "descripcion": r[1],
                "valor_minimo": float(r[2]) if r[2] is not None else None,
                "valor_maximo": float(r[3]) if r[3] is not None else None,
                "id_tipo_etapa": r[4], "id_unidad_medida": r[5]
            }
        except psycopg2.Error as e:
            app.logger.error(f"Error en getById parametros: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, d):
        sql = """INSERT INTO parametros_control_calidad
                 (descripcion, valor_minimo, valor_maximo, id_tipo_etapa, id_unidad_medida)
                 VALUES (%s,%s,%s,%s,%s) RETURNING id_parametro"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (d['descripcion'], d['valor_minimo'], d['valor_maximo'],
                              d['id_tipo_etapa'], d['id_unidad_medida']))
            idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar parametros: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, d):
        sql = """UPDATE parametros_control_calidad SET
                    descripcion = %s, valor_minimo = %s, valor_maximo = %s,
                    id_tipo_etapa = %s, id_unidad_medida = %s
                 WHERE id_parametro = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (d['descripcion'], d['valor_minimo'], d['valor_maximo'],
                              d['id_tipo_etapa'], d['id_unidad_medida'], id))
            con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update parametros: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM parametros_control_calidad WHERE id_parametro = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete parametros: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def getCombos(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT id_etapa, descripcion FROM tipo_etapas ORDER BY descripcion")
            etapas = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            cur.execute("SELECT id_unidad_medida, descripcion FROM unidad_medida ORDER BY descripcion")
            unidades = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            return {"etapas": etapas, "unidades": unidades}
        except psycopg2.Error as e:
            app.logger.error(f"Error en getCombos parametros: {e}")
            return {"etapas": [], "unidades": []}
        finally:
            cur.close(); con.close()
