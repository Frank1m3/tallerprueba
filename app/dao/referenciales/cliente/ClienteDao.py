from flask import current_app as app
from app.conexion.Conexion import Conexion


class ClienteDao:

    def getClientes(self):
        sql = """
        SELECT id_clie, clie_nombre, clie_ci, clie_direccion, clie_telefono, cta_cobrar
        FROM cliente
        ORDER BY clie_nombre
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [{
                "id_cliente":  f[0],
                "nombre":      f[1] or '',
                "cedula":      f[2] or '',
                "direccion":   f[3] or '',
                "telefono":    f[4] or '',
                "cta_cobrar":  f[5] or False
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener clientes: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getClienteById(self, id_cliente):
        sql = """
        SELECT id_clie, clie_nombre, clie_ci, clie_direccion, clie_telefono, cta_cobrar
        FROM cliente
        WHERE id_clie = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_cliente,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_cliente": f[0],
                "nombre":     f[1] or '',
                "cedula":     f[2] or '',
                "direccion":  f[3] or '',
                "telefono":   f[4] or '',
                "cta_cobrar": f[5] or False
            }
        except Exception as e:
            app.logger.error(f"Error al obtener cliente por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardarCliente(self, nombre, cedula, direccion, telefono, cta_cobrar=False):
        sql = """
        INSERT INTO cliente (clie_nombre, clie_ci, clie_direccion, clie_telefono, cta_cobrar)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_clie
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (nombre, cedula, direccion, telefono, cta_cobrar))
            id_clie = cur.fetchone()[0]
            con.commit()
            return True, id_clie
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al guardar cliente: {e}")
            return False, str(e)
        finally:
            cur.close()
            con.close()

    def updateCliente(self, id_cliente, nombre, cedula, direccion, telefono, cta_cobrar=False):
        sql = """
        UPDATE cliente
        SET clie_nombre = %s, clie_ci = %s, clie_direccion = %s,
            clie_telefono = %s, cta_cobrar = %s
        WHERE id_clie = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (nombre, cedula, direccion, telefono, cta_cobrar, id_cliente))
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al actualizar cliente: {e}")
            return False, str(e)
        finally:
            cur.close()
            con.close()

    def deleteCliente(self, id_cliente):
        sql = "DELETE FROM cliente WHERE id_clie = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_cliente,))
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al eliminar cliente: {e}")
            return False, str(e)
        finally:
            cur.close()
            con.close()