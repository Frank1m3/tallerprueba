from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class ItemDao:

    # ---- Listado con descripciones de las FK (para la tabla) ----
    def getItems(self):
        sql = """
            SELECT i.id_item, i.item_code, i.descripcion,
                   i.precio_unitario, i.cantidad_minima, i.activo,
                   u.descripcion  AS unidad_desc,
                   ti.descripcion AS tipo_item_desc,
                   p.prov_nombre  AS proveedor_desc
            FROM item i
            LEFT JOIN unidad_medida u ON u.id_unidad_medida = i.unidad_med
            LEFT JOIN tipo_item ti    ON ti.id_tipo_item    = i.id_tipo_item
            LEFT JOIN proveedor p     ON p.id_proveedor     = i.id_proveedor
            ORDER BY i.descripcion
        """
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                "id": r[0], "item_code": r[1], "descripcion": r[2],
                "precio_unitario": float(r[3]) if r[3] is not None else None,
                "cantidad_minima": float(r[4]) if r[4] is not None else None,
                "activo": r[5],
                "unidad_desc": r[6], "tipo_item_desc": r[7], "proveedor_desc": r[8]
            } for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en getItems: {e}"); return []
        finally:
            cur.close(); con.close()

    # ---- Un item con sus FK crudas (para el formulario) ----
    def getItemById(self, id):
        sql = """SELECT id_item, item_code, descripcion, unidad_med, id_tipo_impuesto,
                        precio_unitario, id_proveedor, id_tipo_item, cantidad_minima, activo
                 FROM item WHERE id_item = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); r = cur.fetchone()
            if not r: return None
            return {
                "id": r[0], "item_code": r[1], "descripcion": r[2],
                "unidad_med": r[3], "id_tipo_impuesto": r[4],
                "precio_unitario": float(r[5]) if r[5] is not None else None,
                "id_proveedor": r[6], "id_tipo_item": r[7],
                "cantidad_minima": float(r[8]) if r[8] is not None else None,
                "activo": r[9]
            }
        except psycopg2.Error as e:
            app.logger.error(f"Error en getItemById: {e}"); return None
        finally:
            cur.close(); con.close()

    def guardar(self, d):
        sql = """INSERT INTO item
                 (item_code, descripcion, unidad_med, id_tipo_impuesto,
                  precio_unitario, id_proveedor, id_tipo_item, cantidad_minima, activo)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_item"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (d['item_code'], d['descripcion'], d['unidad_med'],
                              d['id_tipo_impuesto'], d['precio_unitario'], d['id_proveedor'],
                              d['id_tipo_item'], d['cantidad_minima'], d['activo']))
            idr = cur.fetchone()[0]; con.commit(); return idr
        except psycopg2.Error as e:
            app.logger.error(f"Error en guardar item: {e}"); con.rollback(); return None
        finally:
            cur.close(); con.close()

    def update(self, id, d):
        sql = """UPDATE item SET
                    item_code = %s, descripcion = %s, unidad_med = %s, id_tipo_impuesto = %s,
                    precio_unitario = %s, id_proveedor = %s, id_tipo_item = %s,
                    cantidad_minima = %s, activo = %s
                 WHERE id_item = %s"""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (d['item_code'], d['descripcion'], d['unidad_med'],
                              d['id_tipo_impuesto'], d['precio_unitario'], d['id_proveedor'],
                              d['id_tipo_item'], d['cantidad_minima'], d['activo'], id))
            con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en update item: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    def delete(self, id):
        sql = "DELETE FROM item WHERE id_item = %s"
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id,)); con.commit(); return cur.rowcount > 0
        except psycopg2.Error as e:
            app.logger.error(f"Error en delete item: {e}"); con.rollback(); return False
        finally:
            cur.close(); con.close()

    # ---- Combos para los selects del formulario ----
    def getCombos(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT id_unidad_medida, descripcion FROM unidad_medida ORDER BY descripcion")
            unidades = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            cur.execute("SELECT id_tipo_item, descripcion FROM tipo_item ORDER BY descripcion")
            tipos_item = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            cur.execute("SELECT id_tipo_impuesto, descripcion FROM tipo_impuesto ORDER BY descripcion")
            impuestos = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            cur.execute("SELECT id_proveedor, prov_nombre FROM proveedor ORDER BY prov_nombre")
            proveedores = [{"id": r[0], "descripcion": r[1]} for r in cur.fetchall()]
            return {"unidades": unidades, "tipos_item": tipos_item,
                    "impuestos": impuestos, "proveedores": proveedores}
        except psycopg2.Error as e:
            app.logger.error(f"Error en getCombos item: {e}")
            return {"unidades": [], "tipos_item": [], "impuestos": [], "proveedores": []}
        finally:
            cur.close(); con.close()
