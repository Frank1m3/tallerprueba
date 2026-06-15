from flask import current_app as app
from app.conexion.Conexion import Conexion


class ArqueoDao:

    # Mapeo id forma_pago -> columna de arqueo_caja
    MAPEO_ARQUEO = {
        1: 'total_efectivo',          # efectivo
        3: 'total_cheque',            # cheque
        4: 'total_tarjeta_debito',    # tarjeta débito
        5: 'total_tarjeta_credito',   # tarjeta crédito
        6: 'total_qr',                # QR
        7: 'total_otros',             # Crédito (Cuenta Corriente)
        8: 'total_otros',             # Vale o Cupón
    }
    ID_EFECTIVO = 1

    # ================================
    # Aperturas activas
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
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                "id_apertura": f[0], "nro_turno": f[1], "fiscal": f[2] or '',
                "cajero": f[3] or '', "registro": f[4] or '',
                "monto_inicial": float(f[5]) if f[5] else 0.0, "estado": f[6]
            } for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener aperturas activas: {e}")
            return []
        finally:
            cur.close(); con.close()

    # ================================
    # Resumen de ventas por forma de pago de una apertura  (CORREGIDO)
    # Une por v.id_apertura. Lista TODAS las formas (total 0 si no hubo).
    # Requiere FK cobro_cab.id_venta_cab.
    # ================================
    def getResumenVentasPorApertura(self, id_apertura):
        sql = """
        SELECT fp.id, fp.descripcion,
               COALESCE(SUM(cd.monto_cobrado), 0) AS total
        FROM formas_pago fp
        LEFT JOIN cobro_det cd ON cd.id_forma_cobro = fp.id
        LEFT JOIN cobro_cab cc ON cc.id_cobro_cab   = cd.id_cobro_cab
        LEFT JOIN venta_cab v  ON v.id_venta_cab    = cc.id_venta_cab
                              AND v.id_apertura      = %s
                              AND v.estado           = 'PAGADO'
        GROUP BY fp.id, fp.descripcion
        ORDER BY fp.id
        """
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            return [{
                "id_forma": f[0], "forma_pago": f[1], "total": float(f[2])
            } for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener resumen ventas: {e}")
            return []
        finally:
            cur.close(); con.close()

    # ================================
    # Datos completos de una apertura
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
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_apertura": f[0], "nro_turno": f[1], "fiscal": f[2] or '',
                "cajero": f[3] or '', "registro": f[4] or '',
                "monto_inicial": float(f[5]) if f[5] else 0.0, "estado": f[6],
                "fecha_apertura": str(f[7]) if f[7] else ''
            }
        except Exception as e:
            app.logger.error(f"Error al obtener apertura: {e}")
            return None
        finally:
            cur.close(); con.close()

    # ================================
    # FINALIZAR ARQUEO (transaccional)
    #   - calcula esperado por forma desde el sistema
    #   - guarda arqueo_caja con el contado por forma + totales
    #   - cierra la apertura (estado='cerrado')
    #   - cierra la fila de 'cierres' que dejó abierta el trigger
    #
    # conteos = [{ "id_forma": int, "monto_contado": float }, ...]
    # ================================
    def finalizarArqueo(self, id_apertura, conteos, observacion=''):
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute("BEGIN")

            # 1) Apertura activa + datos del turno
            cur.execute("""
                SELECT a.nro_turno, a.monto_inicial,
                       UPPER(f2.nombres || ' ' || f2.apellidos) AS cajero,
                       UPPER(f1.nombres || ' ' || f1.apellidos) AS fiscal
                FROM aperturas a
                LEFT JOIN funcionarios f1 ON f1.fun_id = a.clave_fiscal
                LEFT JOIN funcionarios f2 ON f2.fun_id = a.cajero
                WHERE a.id_apertura = %s AND a.estado = 'activo'
                FOR UPDATE
            """, (id_apertura,))
            ap = cur.fetchone()
            if not ap:
                cur.execute("ROLLBACK")
                return {"error": "La apertura no existe o no está activa."}
            nro_turno     = ap[0]
            monto_inicial = float(ap[1] or 0)
            cajero        = ap[2] or ''
            fiscal        = ap[3] or ''

            # 2) Esperado por forma (ventas del turno)
            cur.execute("""
                SELECT cd.id_forma_cobro, COALESCE(SUM(cd.monto_cobrado), 0)
                FROM venta_cab v
                JOIN cobro_cab cc ON cc.id_venta_cab = v.id_venta_cab
                JOIN cobro_det cd ON cd.id_cobro_cab = cc.id_cobro_cab
                WHERE v.id_apertura = %s AND v.estado = 'PAGADO'
                GROUP BY cd.id_forma_cobro
            """, (id_apertura,))
            esperado = {r[0]: float(r[1]) for r in cur.fetchall()}
            total_sistema_ventas = sum(esperado.values())

            # 3) Contado del cajero, mapeado a columnas de arqueo_caja
            contado = {int(c['id_forma']): float(c.get('monto_contado', 0) or 0) for c in conteos}
            cols = {v: 0.0 for v in set(self.MAPEO_ARQUEO.values())}
            for id_forma, monto in contado.items():
                col = self.MAPEO_ARQUEO.get(id_forma, 'total_otros')
                cols[col] += monto

            total_arqueo  = sum(contado.values())
            # Lo esperado físico incluye el fondo inicial (en efectivo)
            total_sistema = total_sistema_ventas + monto_inicial
            diferencia    = total_arqueo - total_sistema

            # 4) Insertar arqueo
            cur.execute("""
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
                    %s, 'finalizado'
                ) RETURNING id_arqueo
            """, (
                id_apertura, nro_turno, cajero, fiscal, monto_inicial,
                cols['total_efectivo'], cols['total_tarjeta_credito'], cols['total_tarjeta_debito'],
                cols['total_cheque'], cols['total_qr'], cols['total_otros'],
                total_sistema, total_arqueo, diferencia,
                observacion
            ))
            id_arqueo = cur.fetchone()[0]

            # 5) Cerrar la apertura (no dispara el trigger de 'anulado')
            cur.execute("""
                UPDATE aperturas
                SET estado = 'cerrado', fec_cierre_turno = NOW()
                WHERE id_apertura = %s AND estado = 'activo'
            """, (id_apertura,))

            # 6) Cerrar la fila de 'cierres' que creó el trigger al abrir
            cur.execute("""
                UPDATE cierres
                SET estado = 'cerrado',
                    monto_final = %s,
                    diferencia  = %s,
                    observacion = COALESCE(observacion, '') || %s
                WHERE id_apertura = %s AND estado = 'abierto'
            """, (total_arqueo, diferencia, f' | Arqueo #{id_arqueo}', id_apertura))

            cur.execute("COMMIT")
            return {
                "id_arqueo": id_arqueo,
                "total_sistema": total_sistema,
                "total_arqueo": total_arqueo,
                "diferencia": diferencia,
                "monto_inicial": monto_inicial
            }
        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al finalizar arqueo: {e}")
            return {"error": "Error interno al finalizar el arqueo."}
        finally:
            cur.close(); con.close()

    # ================================
    # Listado de arqueos
    # ================================
    def getArqueos(self):
        sql = """
        SELECT id_arqueo, id_apertura, nro_turno, cajero, fiscal,
               monto_inicial, total_sistema, total_arqueo, diferencia,
               estado, to_char(fecha_arqueo, 'DD/MM/YYYY HH24:MI') AS fecha_arqueo
        FROM arqueo_caja
        ORDER BY fecha_arqueo DESC
        """
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                "id_arqueo": f[0], "id_apertura": f[1], "nro_turno": f[2],
                "cajero": f[3] or '', "fiscal": f[4] or '',
                "monto_inicial": float(f[5]) if f[5] else 0.0,
                "total_sistema": float(f[6]) if f[6] else 0.0,
                "total_arqueo": float(f[7]) if f[7] else 0.0,
                "diferencia": float(f[8]) if f[8] else 0.0,
                "estado": f[9], "fecha_arqueo": f[10] or ''
            } for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener arqueos: {e}")
            return []
        finally:
            cur.close(); con.close()

    # ================================
    # Arqueo por ID
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
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id_arqueo,))
            f = cur.fetchone()
            if not f:
                return None
            return {
                "id_arqueo": f[0], "id_apertura": f[1], "nro_turno": f[2],
                "cajero": f[3] or '', "fiscal": f[4] or '',
                "monto_inicial": float(f[5]) if f[5] else 0.0,
                "total_efectivo": float(f[6]) if f[6] else 0.0,
                "total_tarjeta_credito": float(f[7]) if f[7] else 0.0,
                "total_tarjeta_debito": float(f[8]) if f[8] else 0.0,
                "total_cheque": float(f[9]) if f[9] else 0.0,
                "total_qr": float(f[10]) if f[10] else 0.0,
                "total_otros": float(f[11]) if f[11] else 0.0,
                "total_sistema": float(f[12]) if f[12] else 0.0,
                "total_arqueo": float(f[13]) if f[13] else 0.0,
                "diferencia": float(f[14]) if f[14] else 0.0,
                "observacion": f[15] or '', "estado": f[16],
                "fecha_arqueo": f[17] or ''
            }
        except Exception as e:
            app.logger.error(f"Error al obtener arqueo: {e}")
            return None
        finally:
            cur.close(); con.close()