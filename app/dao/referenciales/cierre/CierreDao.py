from flask import current_app as app
from app.conexion.Conexion import Conexion


class CierreDao:

    # ================================
    # Obtener todos los cierres
    # ================================
    def getCierres(self):
        sql = """
        SELECT id_cierre, id_apertura,
               to_char(registro,      'DD/MM/YYYY HH24:MI:SS') AS registro,
               monto_final, diferencia, observacion, estado, nro_turno,
               UPPER(cajero)  AS cajero,
               UPPER(fiscal)  AS fiscal,
               monto_inicial,
               to_char(hora_apertura, 'DD/MM/YYYY HH24:MI:SS') AS hora_apertura
        FROM cierres
        ORDER BY registro DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [{
                "id_cierre":     f[0],
                "id_apertura":   f[1],
                "registro":      f[2],
                "monto_final":   float(f[3]) if f[3] is not None else 0.0,
                "diferencia":    float(f[4]) if f[4] is not None else 0.0,
                "observacion":   f[5] or '',
                "estado":        f[6],
                "nro_turno":     f[7],
                "cajero":        f[8] or '',
                "fiscal":        f[9] or '',
                "monto_inicial": float(f[10]) if f[10] is not None else 0.0,
                "hora_apertura": f[11] or '',
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener cierres: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener cierre por ID
    # ================================
    def getCierreById(self, id_cierre):
        sql = """
        SELECT id_cierre, id_apertura,
               to_char(registro,      'DD/MM/YYYY HH24:MI:SS') AS registro,
               monto_final, diferencia, observacion, estado, nro_turno,
               UPPER(cajero)  AS cajero,
               UPPER(fiscal)  AS fiscal,
               monto_inicial,
               to_char(hora_apertura, 'DD/MM/YYYY HH24:MI:SS') AS hora_apertura
        FROM cierres
        WHERE id_cierre = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_cierre,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_cierre":     f[0],
                "id_apertura":   f[1],
                "registro":      f[2],
                "monto_final":   float(f[3]) if f[3] is not None else 0.0,
                "diferencia":    float(f[4]) if f[4] is not None else 0.0,
                "observacion":   f[5] or '',
                "estado":        f[6],
                "nro_turno":     f[7],
                "cajero":        f[8] or '',
                "fiscal":        f[9] or '',
                "monto_inicial": float(f[10]) if f[10] is not None else 0.0,
                "hora_apertura": f[11] or '',
            }
        except Exception as e:
            app.logger.error(f"Error al obtener cierre por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Guardar cierre
    # ================================
    def guardarCierre(self, id_apertura, monto_final, monto_inicial,
                      diferencia=None, observacion=None,
                      nro_turno=None, cajero=None, fiscal=None,
                      hora_apertura=None):
        sql = """
        INSERT INTO cierres
            (id_apertura, monto_final, monto_inicial, diferencia,
             observacion, estado, nro_turno, cajero, fiscal, hora_apertura)
        VALUES
            (%s, %s, %s, %s,
             %s, 'abierto', %s, %s, %s, %s)
        RETURNING id_cierre
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (
                id_apertura, monto_final, monto_inicial, diferencia,
                observacion, nro_turno, cajero, fiscal, hora_apertura
            ))
            id_cierre = cur.fetchone()[0]
            con.commit()
            return id_cierre
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al guardar cierre: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Cerrar cierre (estado → 'cerrado') y cierra la apertura en una transacción
    # ================================
    def cerrarCierre(self, id_cierre):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("BEGIN")

            # Obtener id_apertura del cierre
            cur.execute("""
                SELECT id_apertura FROM cierres
                WHERE id_cierre = %s AND estado = 'abierto'
            """, (id_cierre,))
            row = cur.fetchone()
            if not row:
                cur.execute("ROLLBACK")
                return False

            id_apertura = row[0]

            # Cerrar el cierre
            cur.execute("""
                UPDATE cierres
                SET estado = 'cerrado'
                WHERE id_cierre = %s AND estado = 'abierto'
            """, (id_cierre,))

            # Cerrar la apertura asociada
            cur.execute("""
                UPDATE aperturas
                SET estado = 'cerrado', fec_cierre_turno = NOW()
                WHERE id_apertura = %s AND estado = 'activo'
            """, (id_apertura,))

            cur.execute("COMMIT")
            return True

        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al cerrar cierre: {e}")
            return False
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener total de ventas de una apertura
    # Usa id_apertura directo en venta_cab (exacto, sin depender de fechas)
    # ================================
    def getTotalVentasPorApertura(self, id_apertura):
        sql = """
        SELECT
            COALESCE(SUM(v.total_venta), 0) AS total_ventas,
            COUNT(v.id_venta_cab)           AS cant_ventas
        FROM venta_cab v
        WHERE v.id_apertura = %s
          AND v.estado = 'PAGADO'
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            f = cur.fetchone()
            return {
                "total_ventas": float(f[0]) if f[0] else 0.0,
                "cant_ventas":  int(f[1]) if f[1] else 0
            }
        except Exception as e:
            app.logger.error(f"Error al obtener total ventas: {e}")
            return {"total_ventas": 0.0, "cant_ventas": 0}
        finally:
            cur.close()
            con.close()