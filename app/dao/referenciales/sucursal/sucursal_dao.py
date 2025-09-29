from flask import current_app as app
from app.conexion.Conexion import Conexion

class SucursalDao:

    def getSucursales(self):
        sql = """
        SELECT id_sucursal,
               descripcion,
               activo,
               id_fiscal,
               direccion,
               departamento,
               ciudad
        FROM sucursal
        ORDER BY id_sucursal
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            lista = []
            for f in filas:
                lista.append({
                    "id_sucursal": f[0],
                    "descripcion": f[1],
                    "activo": f[2],
                    "id_fiscal": f[3],
                    "direccion": f[4],
                    "departamento": f[5],
                    "ciudad": f[6]
                })
            return lista
        except Exception as e:
            app.logger.error(f"Error al obtener sucursales: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getSucursalById(self, id_sucursal):
        sql = """
        SELECT id_sucursal,
               descripcion,
               activo,
               id_fiscal,
               direccion,
               departamento,
               ciudad
        FROM sucursal
        WHERE id_sucursal = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal,))
            f = cur.fetchone()
            if f:
                return {
                    "id_sucursal": f[0],
                    "descripcion": f[1],
                    "activo": f[2],
                    "id_fiscal": f[3],
                    "direccion": f[4],
                    "departamento": f[5],
                    "ciudad": f[6]
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener sucursal por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardarSucursal(self, descripcion, activo=True,
                        id_fiscal=None, direccion=None,
                        departamento=None, ciudad=None):
        sql = """
        INSERT INTO sucursal
        (descripcion, activo, id_fiscal, direccion, departamento, ciudad)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, activo, id_fiscal,
                              direccion, departamento, ciudad))
            con.commit()
            return True
        except Exception as e:
            app.logger.error(f"Error al insertar sucursal: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def updateSucursal(self, id_sucursal, descripcion, activo=True,
                       id_fiscal=None, direccion=None,
                       departamento=None, ciudad=None):
        sql = """
        UPDATE sucursal
        SET descripcion = %s,
            activo = %s,
            id_fiscal = %s,
            direccion = %s,
            departamento = %s,
            ciudad = %s
        WHERE id_sucursal = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, activo, id_fiscal,
                              direccion, departamento, ciudad, id_sucursal))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al actualizar sucursal: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    def deleteSucursal(self, id_sucursal):
        sql = "DELETE FROM sucursal WHERE id_sucursal = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al eliminar sucursal: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ---------------- Nuevo método para traer depósitos ----------------
    def get_sucursal_depositos(self, id_sucursal):
        """
        Devuelve los depósitos de una sucursal junto con stock actual por depósito.
        """
        sql = """
        SELECT d.id_deposito,
               d.nombre_deposito,
               COALESCE(s.stock,0) as stock
        FROM deposito d
        LEFT JOIN stock s ON s.id_deposito = d.id_deposito
        WHERE d.id_sucursal = %s
        ORDER BY d.id_deposito
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal,))
            filas = cur.fetchall()
            lista = []
            for f in filas:
                lista.append({
                    "id_deposito": f[0],
                    "nombre_deposito": f[1],
                    "stock": float(f[2])
                })
            return lista
        except Exception as e:
            app.logger.error(f"Error al obtener depósitos de sucursal {id_sucursal}: {e}")
            return []
        finally:
            cur.close()
            con.close()
