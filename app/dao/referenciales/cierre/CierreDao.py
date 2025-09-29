from flask import current_app as app
from app.conexion.Conexion import Conexion

class CierreDao:
    def getCierres(self):
        cierreSQL = """
        SELECT c.id_cierre, c.id_apertura, 
               to_char(c.registro, 'DD/MM/YYYY HH24:MI:SS') as registro, 
               c.monto_final, c.diferencia, c.observacion, c.estado, c.nro_turno,
               cajero.nombres || ' ' || cajero.apellidos AS cajero,  -- Nombre completo del cajero
               fiscal.nombres || ' ' || fiscal.apellidos AS fiscal,  -- Nombre completo del fiscal
               a.monto_inicial AS monto_inicial,  -- Corregido aquí
               to_char(c.registro, 'DD/MM/YYYY HH24:MI:SS') as hora_apertura
        FROM cierres c
        JOIN aperturas a ON c.id_apertura = a.id_apertura
        JOIN personas cajero ON a.cajero = cajero.id_persona
        JOIN personas fiscal ON a.clave_fiscal = fiscal.id_persona
        ORDER BY c.registro DESC
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(cierreSQL)
            datos = cur.fetchall()

            cierres = []
            for c in datos:
                cierres.append({
                    "id_cierre": c[0],
                    "id_apertura": c[1],
                    "registro": c[2],
                    "monto_final": float(c[3]),
                    "diferencia": float(c[4]) if c[4] is not None else None,
                    "observacion": c[5],
                    "estado": c[6],
                    "nro_turno": c[7],
                    "cajero": c[8],  # Nombre completo del cajero
                    "fiscal": c[9],  # Nombre completo del fiscal
                    "monto_inicial": float(c[10]) if c[10] is not None else None,  # Ahora es "a.monto_inicial"
                    "hora_apertura": c[11]
                })

            return cierres

        except con.Error as e:
            app.logger.error(f"Error al obtener cierres: {e}")
            return []

        finally:
            cur.close()
            con.close()

    def getCierreById(self, id_cierre):
        cierreSQL = """
        SELECT c.id_cierre, c.id_apertura, c.registro, c.monto_final, c.diferencia, 
               c.observacion, c.estado, c.nro_turno,
               c.cajero, c.fiscal, c.monto_inicial, c.hora_apertura
        FROM cierres c
        WHERE c.id_cierre = %s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(cierreSQL, (id_cierre,))
            c = cur.fetchone()

            if c:
                return {
                    "id_cierre": c[0],
                    "id_apertura": c[1],
                    "registro": c[2],
                    "monto_final": float(c[3]),
                    "diferencia": float(c[4]) if c[4] is not None else None,
                    "observacion": c[5],
                    "estado": c[6],
                    "nro_turno": c[7],
                    "cajero": c[8],
                    "fiscal": c[9],
                    "monto_inicial": float(c[10]) if c[10] is not None else None,  # Ahora es "c.monto_inicial"
                    "hora_apertura": c[11]
                }
            return None

        except con.Error as e:
            app.logger.error(f"Error al obtener cierre por ID: {e}")
            return None

        finally:
            cur.close()
            con.close()

    def cerrarCierre(self, id_cierre):
        updateSQL = """
        UPDATE cierres
        SET estado = 'cerrado'
        WHERE id_cierre = %s AND estado = 'abierto'
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(updateSQL, (id_cierre,))
            con.commit()
            return cur.rowcount > 0  

        except con.Error as e:
            app.logger.error(f"Error al cerrar el cierre: {e}")
            return False

        finally:
            cur.close()
            con.close()
