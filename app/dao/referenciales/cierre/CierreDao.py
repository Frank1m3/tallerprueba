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
    # Cerrar cierre (estado → 'cerrado')
    # ================================
    def cerrarCierre(self, id_cierre):
        sql = """
        UPDATE cierres
        SET estado = 'cerrado'
        WHERE id_cierre = %s AND estado = 'abierto'
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_cierre,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al cerrar cierre: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()