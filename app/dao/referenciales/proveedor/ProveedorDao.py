from flask import current_app as app
from app.conexion.Conexion import Conexion

class ProveedorDao:

    def getProveedores(self):
        sql = """
        SELECT id_proveedor, prov_nombre, prov_ruc, prov_razon_social, prov_telefono, prov_direccion, prov_email
        FROM public.proveedor
        ORDER BY id_proveedor
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            proveedores = cur.fetchall()
            lista = []
            for p in proveedores:
                lista.append({
                    "id_proveedor": p[0],
                    "nombre": p[1],
                    "ruc": p[2],
                    "razon_social": p[3],
                    "telefono": p[4],
                    "direccion": p[5],
                    "email": p[6]
                })
            return lista
        except Exception as e:
            app.logger.error(f"Error en getProveedores: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getProveedorById(self, id_proveedor):
        sql = """
        SELECT id_proveedor, prov_nombre, prov_ruc, prov_razon_social, prov_telefono, prov_direccion, prov_email
        FROM public.proveedor
        WHERE id_proveedor = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_proveedor,))
            p = cur.fetchone()
            if p:
                return {
                    "id_proveedor": p[0],
                    "nombre": p[1],
                    "ruc": p[2],
                    "razon_social": p[3],
                    "telefono": p[4],
                    "direccion": p[5],
                    "email": p[6]
                }
            return None
        except Exception as e:
            app.logger.error(f"Error en getProveedorById: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardarProveedor(self, nombre, ruc, razon_social, telefono, direccion=None, email=None):
        sql = """
        INSERT INTO public.proveedor (prov_nombre, prov_ruc, prov_razon_social, prov_telefono, prov_direccion, prov_email)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (nombre, ruc, razon_social, telefono, direccion, email))
            con.commit()
            return True
        except Exception as e:
            app.logger.error(f"Error en guardarProveedor: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def updateProveedor(self, id_proveedor, nombre, ruc, razon_social, telefono, direccion=None, email=None):
        sql = """
        UPDATE public.proveedor
        SET prov_nombre = %s,
            prov_ruc = %s,
            prov_razon_social = %s,
            prov_telefono = %s,
            prov_direccion = %s,
            prov_email = %s
        WHERE id_proveedor = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (nombre, ruc, razon_social, telefono, direccion, email, id_proveedor))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error en updateProveedor: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def deleteProveedor(self, id_proveedor):
        sql = "DELETE FROM public.proveedor WHERE id_proveedor = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_proveedor,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error en deleteProveedor: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()
