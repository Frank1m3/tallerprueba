from flask import current_app as app
from app.conexion.Conexion import Conexion


class FacturaCompraDao:
    """
    Factura de Compra: cierra el ciclo Solicitud -> Presupuesto -> Pedido ->
    Recepción -> Factura. Una factura corresponde a una Recepción completa
    (no se duplica el detalle por ítem). Al insertarse, también se registra
    en libro_compras (tabla que ya existía en la base pero nunca se usaba).
    """

    ESTADOS_VALIDOS = ('PENDIENTE', 'PAGADA', 'ANULADA')

    # ================================
    # Recepciones confirmadas que todavía no tienen factura
    # ================================
    def obtener_recepciones_disponibles(self):
        sql = """
            SELECT r.id_recepcion, r.nro_recepcion, r.fecha_recepcion,
                   r.id_proveedor, p.prov_nombre,
                   COALESCE((
                       SELECT SUM(rd.cantidad_recibida * pd.costo_unitario)
                       FROM recepcion_det rd
                       LEFT JOIN pedido_compra_det pd ON pd.id_pedido_compra_det = rd.id_pedido_det
                       WHERE rd.id_recepcion = r.id_recepcion
                   ), 0) AS monto_sugerido
            FROM recepcion_cab r
            LEFT JOIN proveedor p ON p.id_proveedor = r.id_proveedor
            LEFT JOIN factura_compra_cab fc ON fc.id_recepcion = r.id_recepcion
            WHERE r.estado = 'CONFIRMADO' AND fc.id_factura IS NULL
            ORDER BY r.id_recepcion DESC
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                'id_recepcion': r[0], 'nro_recepcion': r[1],
                'fecha_recepcion': r[2].strftime("%Y-%m-%d") if r[2] else None,
                'id_proveedor': r[3], 'proveedor_nombre': r[4] or '',
                'monto_sugerido': float(r[5])
            } for r in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener recepciones disponibles: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Listar facturas (para el índice)
    # ================================
    def listar(self):
        sql = """
            SELECT f.id_factura, f.nro_factura, f.fecha_emision, f.fecha_vencimiento,
                   p.prov_nombre, r.nro_recepcion, f.monto_total, f.estado, f.fecha_pago
            FROM factura_compra_cab f
            LEFT JOIN proveedor p ON p.id_proveedor = f.id_proveedor
            LEFT JOIN recepcion_cab r ON r.id_recepcion = f.id_recepcion
            ORDER BY f.id_factura DESC
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            return [{
                'id_factura': r[0], 'nro_factura': r[1],
                'fecha_emision': r[2].strftime("%Y-%m-%d") if r[2] else None,
                'fecha_vencimiento': r[3].strftime("%Y-%m-%d") if r[3] else None,
                'proveedor': r[4] or '', 'nro_recepcion': r[5],
                'monto_total': float(r[6]) if r[6] is not None else 0,
                'estado': r[7],
                'fecha_pago': r[8].strftime("%Y-%m-%d") if r[8] else None
            } for r in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al listar facturas: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Insertar factura + su entrada correspondiente en libro_compras
    # ================================
    def insertar(self, data: dict) -> bool:
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            con.autocommit = False
            cur.execute("""
                INSERT INTO factura_compra_cab
                (nro_factura, fecha_emision, fecha_vencimiento, id_proveedor,
                 id_recepcion, monto_total, id_tipo_impuesto, archivo, estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'PENDIENTE')
                RETURNING id_factura
            """, (
                data.get('nro_factura'),
                data.get('fecha_emision'),
                data.get('fecha_vencimiento'),
                data.get('id_proveedor'),
                data.get('id_recepcion'),
                data.get('monto_total') or 0,
                data.get('id_tipo_impuesto'),
                data.get('archivo'),
            ))
            id_factura = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO libro_compras (id_factura, fecha_emision, tipo_impuesto, monto, fecha_creacion)
                VALUES (%s, %s, %s, %s, CURRENT_DATE)
            """, (
                id_factura,
                data.get('fecha_emision'),
                data.get('id_tipo_impuesto'),
                data.get('monto_total') or 0,
            ))

            con.commit()
            return True
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al insertar factura: {e}")
            return False
        finally:
            con.autocommit = True
            cur.close()
            con.close()

    # ================================
    # Cambiar estado (libre); al pasar a PAGADA registra fecha_pago
    # ================================
    def cambiar_estado(self, id_factura, nuevo_estado):
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            return False, f"Estado inválido. Use uno de: {', '.join(self.ESTADOS_VALIDOS)}"
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            if nuevo_estado == 'PAGADA':
                cur.execute(
                    "UPDATE factura_compra_cab SET estado = %s, fecha_pago = CURRENT_DATE WHERE id_factura = %s",
                    (nuevo_estado, id_factura)
                )
            else:
                cur.execute(
                    "UPDATE factura_compra_cab SET estado = %s, fecha_pago = NULL WHERE id_factura = %s",
                    (nuevo_estado, id_factura)
                )
            if cur.rowcount == 0:
                con.rollback()
                return False, 'No existe la factura'
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al cambiar estado de factura {id_factura}: {e}")
            return False, str(e)
        finally:
            cur.close()
            con.close()
