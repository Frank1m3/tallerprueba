from flask import current_app as app
from app.conexion.Conexion import Conexion


class ArqueoDao:

    # ================================
    # Obtener aperturas activas para seleccionar
    # ================================
    def getAperturasActivas(self):
        sql = """
        SELECT a.id_apertura, a.nro_turno,
               UPPER(f1.nombres || ' ' || f1.apellidos) AS fiscal,
               UPPER(f2.nombres || ' ' || f2.apellidos) AS cajero,
               to_char(a.registro, 'DD/MM/YYYY HH24:MI:SS') AS registro,
               a.monto_inicial, a.estado
        FROM aperturas a
        LEFT JOIN funcionarios f1 ON f1.fun_id = a.clave_fiscal
        LEFT JOIN funcionarios f2 ON f2.fun_id = a.cajero
        WHERE a.estado = 'activo'
        ORDER BY a.nro_turno DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [{
                "id_apertura":  f[0],
                "nro_turno":    f[1],
                "fiscal":       f[2] or '',
                "cajero":       f[3] or '',
                "registro":     f[4] or '',
                "monto_inicial":float(f[5]) if f[5] else 0.0,
                "estado":       f[6]
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener aperturas activas: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener resumen de ventas por forma de pago de una apertura
    # ================================
    def getResumenVentasPorApertura(self, id_apertura):
        sql = """
        SELECT
            fp.id                   AS id_forma,
            fp.descripcion          AS forma_pago,
            COALESCE(SUM(cd.monto_cobrado), 0) AS total
        FROM formas_pago fp
        LEFT JOIN cobro_det cd ON cd.id_forma_cobro = fp.id
        LEFT JOIN cobro_cab cc ON cc.id_cobro_cab = cd.id_cobro_cab
        LEFT JOIN venta_cab v  ON cc.referencia = 'VENTA-' || v.id_venta_cab
        LEFT JOIN aperturas a  ON v.fecha_venta = DATE(a.registro)
                               AND (a.fec_cierre_turno IS NULL OR v.fecha_venta <= DATE(a.fec_cierre_turno))
        WHERE a.id_apertura = %s
        GROUP BY fp.id, fp.descripcion
        ORDER BY fp.id
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            filas = cur.fetchall()
            return [{
                "id_forma":  f[0],
                "forma_pago":f[1],
                "total":     float(f[2])
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener resumen ventas: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener totales por forma de pago del día de la apertura
    # (fallback más simple si el JOIN con apertura falla)
    # ================================
    def getTotalesPorFecha(self, fecha):
        sql = """
        SELECT
            fp.id                   AS id_forma,
            fp.descripcion          AS forma_pago,
            COALESCE(SUM(cd.monto_cobrado), 0) AS total,
            COUNT(DISTINCT v.id_venta_cab) AS cant_ventas
        FROM formas_pago fp
        LEFT JOIN cobro_det cd ON cd.id_forma_cobro = fp.id
        LEFT JOIN cobro_cab cc ON cc.id_cobro_cab = cd.id_cobro_cab
        LEFT JOIN venta_cab v  ON cc.referencia = 'VENTA-' || v.id_venta_cab
                               AND v.fecha_venta = %s
        GROUP BY fp.id, fp.descripcion
        ORDER BY fp.id
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (fecha,))
            filas = cur.fetchall()
            return [{
                "id_forma":   f[0],
                "forma_pago": f[1],
                "total":      float(f[2]),
                "cant_ventas":f[3]
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener totales por fecha: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener datos completos de una apertura
    # ================================
    def getAperturaById(self, id_apertura):
        sql = """
        SELECT a.id_apertura, a.nro_turno,
               UPPER(f1.nombres || ' ' || f1.apellidos) AS fiscal,
               UPPER(f2.nombres || ' ' || f2.apellidos) AS cajero,
               to_char(a.registro, 'DD/MM/YYYY HH24:MI:SS') AS registro,
               a.monto_inicial, a.estado,
               DATE(a.registro) AS fecha_apertura
        FROM aperturas a
        LEFT JOIN funcionarios f1 ON f1.fun_id = a.clave_fiscal
        LEFT JOIN funcionarios f2 ON f2.fun_id = a.cajero
        WHERE a.id_apertura = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_apertura":  f[0],
                "nro_turno":    f[1],
                "fiscal":       f[2] or '',
                "cajero":       f[3] or '',
                "registro":     f[4] or '',
                "monto_inicial":float(f[5]) if f[5] else 0.0,
                "estado":       f[6],
                "fecha_apertura": str(f[7]) if f[7] else ''
            }
        except Exception as e:
            app.logger.error(f"Error al obtener apertura: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Guardar arqueo
    # ================================
    def guardarArqueo(self, datos):
        sql = """
        INSERT INTO arqueo_caja (
            id_apertura, nro_turno, cajero, fiscal, monto_inicial,
            total_efectivo, total_tarjeta_credito, total_tarjeta_debito,
            total_cheque, total_qr, total_otros,
            total_sistema, total_arqueo, diferencia,
            observacion, estado
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s
        ) RETURNING id_arqueo
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (
                datos['id_apertura'],
                datos['nro_turno'],
                datos['cajero'],
                datos['fiscal'],
                datos['monto_inicial'],
                datos['total_efectivo'],
                datos['total_tarjeta_credito'],
                datos['total_tarjeta_debito'],
                datos['total_cheque'],
                datos['total_qr'],
                datos['total_otros'],
                datos['total_sistema'],
                datos['total_arqueo'],
                datos['diferencia'],
                datos.get('observacion', ''),
                datos.get('estado', 'finalizado')
            ))
            id_arqueo = cur.fetchone()[0]
            con.commit()
            return id_arqueo
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al guardar arqueo: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener todos los arqueos
    # ================================
    def getArqueos(self):
        sql = """
        SELECT id_arqueo, id_apertura, nro_turno, cajero, fiscal,
               monto_inicial, total_sistema, total_arqueo, diferencia,
               estado, to_char(fecha_arqueo, 'DD/MM/YYYY HH24:MI') AS fecha_arqueo
        FROM arqueo_caja
        ORDER BY fecha_arqueo DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [{
                "id_arqueo":      f[0],
                "id_apertura":    f[1],
                "nro_turno":      f[2],
                "cajero":         f[3] or '',
                "fiscal":         f[4] or '',
                "monto_inicial":  float(f[5]) if f[5] else 0.0,
                "total_sistema":  float(f[6]) if f[6] else 0.0,
                "total_arqueo":   float(f[7]) if f[7] else 0.0,
                "diferencia":     float(f[8]) if f[8] else 0.0,
                "estado":         f[9],
                "fecha_arqueo":   f[10] or ''
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener arqueos: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener arqueo por ID
    # ================================
    def getArqueoById(self, id_arqueo):
        sql = """
        SELECT id_arqueo, id_apertura, nro_turno, cajero, fiscal,
               monto_inicial, total_efectivo, total_tarjeta_credito,
               total_tarjeta_debito, total_cheque, total_qr, total_otros,
               total_sistema, total_arqueo, diferencia,
               observacion, estado,
               to_char(fecha_arqueo, 'DD/MM/YYYY HH24:MI') AS fecha_arqueo
        FROM arqueo_caja
        WHERE id_arqueo = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_arqueo,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_arqueo":           f[0],
                "id_apertura":         f[1],
                "nro_turno":           f[2],
                "cajero":              f[3] or '',
                "fiscal":              f[4] or '',
                "monto_inicial":       float(f[5]) if f[5] else 0.0,
                "total_efectivo":      float(f[6]) if f[6] else 0.0,
                "total_tarjeta_credito":float(f[7]) if f[7] else 0.0,
                "total_tarjeta_debito":float(f[8]) if f[8] else 0.0,
                "total_cheque":        float(f[9]) if f[9] else 0.0,
                "total_qr":            float(f[10]) if f[10] else 0.0,
                "total_otros":         float(f[11]) if f[11] else 0.0,
                "total_sistema":       float(f[12]) if f[12] else 0.0,
                "total_arqueo":        float(f[13]) if f[13] else 0.0,
                "diferencia":          float(f[14]) if f[14] else 0.0,
                "observacion":         f[15] or '',
                "estado":              f[16],
                "fecha_arqueo":        f[17] or ''
            }
        except Exception as e:
            app.logger.error(f"Error al obtener arqueo: {e}")
            return None
        finally:
            cur.close()
            con.close()