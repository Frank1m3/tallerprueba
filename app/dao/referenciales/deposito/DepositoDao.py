from flask import current_app as app
from app.conexion.Conexion import Conexion

class DepositoDao:

    # ---------------- Obtener todos los depósitos ----------------
    def getDepositos(self):
        sql = """
        SELECT d.id_deposito,
               d.descripcion,
               d.id_sucursal,
               s.descripcion AS sucursal_nombre
        FROM public.deposito d
        LEFT JOIN public.sucursal s ON d.id_sucursal = s.id_sucursal
        ORDER BY d.id_deposito
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [
                {
                    "id_deposito": f[0],
                    "descripcion": f[1],
                    "id_sucursal": f[2],
                    "sucursal_nombre": f[3] or ''
                } for f in filas
            ]
        except Exception as e:
            app.logger.error(f"Error al obtener depósitos: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ---------------- Obtener depósitos por sucursal ----------------
    def getDepositosPorSucursal(self, id_sucursal):
        sql = """
        SELECT d.id_deposito,
               d.descripcion,
               d.id_sucursal,
               s.descripcion AS sucursal_nombre
        FROM public.deposito d
        LEFT JOIN public.sucursal s ON d.id_sucursal = s.id_sucursal
        WHERE d.id_sucursal = %s
        ORDER BY d.id_deposito
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal,))
            filas = cur.fetchall()
            return [
                {
                    "id_deposito": f[0],
                    "descripcion": f[1],
                    "id_sucursal": f[2],
                    "sucursal_nombre": f[3] or ''
                } for f in filas
            ]
        except Exception as e:
            app.logger.error(f"Error al obtener depósitos por sucursal: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ---------------- Obtener depósito por ID ----------------
    def getDepositoById(self, id_deposito):
        sql = """
        SELECT d.id_deposito,
               d.descripcion,
               d.id_sucursal,
               s.descripcion AS sucursal_nombre
        FROM public.deposito d
        LEFT JOIN public.sucursal s ON d.id_sucursal = s.id_sucursal
        WHERE d.id_deposito = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_deposito,))
            f = cur.fetchone()
            if f:
                return {
                    "id_deposito": f[0],
                    "descripcion": f[1],
                    "id_sucursal": f[2],
                    "sucursal_nombre": f[3] or ''
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener depósito por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ---------------- Guardar depósito ----------------
    def guardarDeposito(self, descripcion, id_sucursal):
        sql = """
        INSERT INTO public.deposito (descripcion, id_sucursal)
        VALUES (%s, %s)
        RETURNING id_deposito
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id_sucursal))
            id_deposito = cur.fetchone()[0]
            con.commit()
            return id_deposito
        except Exception as e:
            app.logger.error(f"Error al guardar depósito: {e}")
            con.rollback()
            return None
        finally:
            cur.close()
            con.close()

    # ---------------- Actualizar depósito ----------------
    def updateDeposito(self, id_deposito, descripcion, id_sucursal):
        sql = """
        UPDATE public.deposito
        SET descripcion = %s,
            id_sucursal = %s
        WHERE id_deposito = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (descripcion, id_sucursal, id_deposito))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al actualizar depósito: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ---------------- Eliminar depósito ----------------
    def deleteDeposito(self, id_deposito):
        sql = "DELETE FROM public.deposito WHERE id_deposito = %s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_deposito,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al eliminar depósito: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ---------------- Obtener stock de un item en un depósito ----------------
    def getStockPorItemYDeposito(self, id_item, id_deposito):
        sql = """
        SELECT cantidad
        FROM public.stock
        WHERE id_item = %s
          AND id_deposito = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_item, id_deposito))
            f = cur.fetchone()
            return float(f[0]) if f else 0
        except Exception as e:
            app.logger.error(f"Error al obtener stock del item {id_item} en depósito {id_deposito}: {e}")
            return 0
        finally:
            cur.close()
            con.close()
