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
    # Registrar cierre: ACTUALIZA la fila que creó el trigger al abrir.
    # Trae la diferencia del ÚLTIMO arqueo del turno (si lo hubo).
    # ================================
    def registrarCierre(self, id_apertura, observacion=None):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("BEGIN")

            # 1) Buscar la fila de cierre creada por el trigger (estado 'abierto')
            cur.execute("""
                SELECT id_cierre, monto_inicial
                FROM cierres
                WHERE id_apertura = %s AND estado = 'abierto'
                FOR UPDATE
            """, (id_apertura,))
            row = cur.fetchone()
            if not row:
                cur.execute("ROLLBACK")
                return {"error": "No hay un cierre abierto para este turno (¿ya fue cerrado?)."}
            id_cierre     = row[0]
            monto_inicial = float(row[1]) if row[1] is not None else 0.0

            # 2) Total de ventas del turno (por id_apertura, exacto)
            cur.execute("""
                SELECT COALESCE(SUM(v.total_venta), 0), COUNT(v.id_venta_cab)
                FROM venta_cab v
                WHERE v.id_apertura = %s AND v.estado = 'PAGADO'
            """, (id_apertura,))
            r = cur.fetchone()
            total_ventas = float(r[0]) if r[0] else 0.0
            cant_ventas  = int(r[1]) if r[1] else 0

            # 3) Último arqueo del turno (el más reciente), si lo hubo
            cur.execute("""
                SELECT total_arqueo, diferencia
                FROM arqueo_caja
                WHERE id_apertura = %s
                ORDER BY id_arqueo DESC
                LIMIT 1
            """, (id_apertura,))
            arq = cur.fetchone()
            if arq:
                total_arqueo = float(arq[0]) if arq[0] is not None else 0.0
                diferencia   = float(arq[1]) if arq[1] is not None else 0.0
                hubo_arqueo  = True
            else:
                total_arqueo = total_ventas
                diferencia   = 0.0          # sin arqueo no hay faltante/sobrante medido
                hubo_arqueo  = False

            # monto_final = lo realmente contado en el arqueo; si no hubo, las ventas
            monto_final = total_arqueo

            # 4) Actualizar la fila del trigger (NO insertar otra)
            cur.execute("""
                UPDATE cierres
                SET monto_final = %s,
                    diferencia  = %s,
                    observacion = %s
                WHERE id_cierre = %s
            """, (monto_final, diferencia, observacion, id_cierre))

            cur.execute("COMMIT")
            return {
                "id_cierre":    id_cierre,
                "monto_final":  monto_final,
                "monto_inicial":monto_inicial,
                "total_ventas": total_ventas,
                "diferencia":   diferencia,
                "cant_ventas":  cant_ventas,
                "hubo_arqueo":  hubo_arqueo
            }
        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al registrar cierre: {e}")
            return {"error": "Error interno al registrar el cierre."}
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

            cur.execute("""
                SELECT id_apertura FROM cierres
                WHERE id_cierre = %s AND estado = 'abierto'
            """, (id_cierre,))
            row = cur.fetchone()
            if not row:
                cur.execute("ROLLBACK")
                return False

            id_apertura = row[0]

            cur.execute("""
                UPDATE cierres
                SET estado = 'cerrado'
                WHERE id_cierre = %s AND estado = 'abierto'
            """, (id_cierre,))

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