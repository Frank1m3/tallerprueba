from flask import current_app as app
from app.conexion.Conexion import Conexion
from datetime import date, timedelta
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compras_dto import RecepcionDto
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compra_detalle_dto import RecepcionDetalleDto
from app.dao.inventario.StockDao import StockDao


class RecepcionDao:

    ESTADOS_RECEPCIONABLES = ('EMITIDA', 'APROBADA', 'PARCIAL', 'PENDIENTE')

    # ============================================
    # Obtener orden de compra por número
    # ============================================
    def obtener_orden_por_nro(self, nro_orden: str):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT
                    oc.id_orden_compra_cab,
                    oc.nro_orden,
                    oc.id_proveedor,
                    p.prov_nombre,
                    oc.fecha_emision,
                    oc.id_sucursal,
                    oc.id_deposito,
                    COALESCE(oc.estado, '') AS estado
                FROM orden_compra_cab oc
                JOIN proveedor p ON p.id_proveedor = oc.id_proveedor
                WHERE oc.nro_orden = %s OR oc.id_orden_compra_cab::text = %s
                LIMIT 1
            """, (nro_orden, nro_orden))
            cab = cur.fetchone()

            if not cab:
                return None

            if cab[7] in ('ANULADO', 'RECIBIDA', 'CERRADA'):
                return {'error': f'La orden está en estado {cab[7]} y no puede recepcionarse.'}

            orden = {
                'id_orden_compra_cab': cab[0],
                'nro_orden': cab[1],
                'id_proveedor': cab[2],
                'proveedor_nombre': cab[3],
                'fecha_emision': cab[4].strftime('%Y-%m-%d') if cab[4] else None,
                'id_sucursal': cab[5],
                'id_deposito': cab[6],
                'estado': cab[7],
                'detalles': []
            }

<<<<<<< Updated upstream
            # Detalles del pedido (incluye id_pedido_det)
            cur.execute("""
                SELECT
                    id_pedido_compra_det,
                    item_code,
                    item_descripcion,
                    cant_pedido,
                    costo_unitario
                FROM pedido_compra_det
                WHERE id_pedido_compra_cab = %s
            """, (cab[0],))
            rows = cur.fetchall()
            for r in rows:
                pedido['detalles'].append({
                    'id_pedido_det': r[0],
                    'item_code': r[1],
                    'descripcion': r[2],
                    'cantidad_pedida': float(r[3]),
                    'costo_unitario': float(r[4])
=======
            cur.execute("""
                SELECT
                    d.id_orden_compra_det,
                    d.id_item,
                    i.item_code,
                    i.descripcion,
                    d.cantidad,
                    d.precio_unitario,
                    COALESCE(SUM(rd.cantidad_recibida), 0) AS ya_recibido
                FROM orden_compra_det d
                JOIN item i ON i.id_item = d.id_item
                LEFT JOIN recepcion_det rd ON rd.id_orden_compra_det = d.id_orden_compra_det
                LEFT JOIN recepcion_cab rc ON rc.id_recepcion = rd.id_recepcion
                    AND rc.estado NOT IN ('ANULADO')
                WHERE d.id_orden_compra_cab = %s
                GROUP BY d.id_orden_compra_det, d.id_item, i.item_code, i.descripcion,
                         d.cantidad, d.precio_unitario
                ORDER BY d.id_orden_compra_det
            """, (cab[0],))
            for r in cur.fetchall():
                pendiente = float(r[4]) - float(r[6])
                if pendiente <= 0:
                    continue
                orden['detalles'].append({
                    'id_orden_compra_det': r[0],
                    'id_item': r[1],
                    'item_code': r[2],
                    'descripcion': r[3],
                    'cantidad_pedida': pendiente,
                    'cantidad_total_oc': float(r[4]),
                    'costo_unitario': float(r[5]) if r[5] else 0.0
>>>>>>> Stashed changes
                })

            if not orden['detalles']:
                return {'error': 'La orden no tiene ítems pendientes de recepción.'}

            return orden

        except Exception as e:
            app.logger.error(f"Error al obtener orden por nro {nro_orden}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    # ============================================
    # Registrar recepción (stock + cuenta a pagar)
    # ============================================
    def agregar_recepcion(self, recepcion_dto: RecepcionDto):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        stock_dao = StockDao()
        try:
<<<<<<< Updated upstream
            cur.execute("""
                INSERT INTO recepcion_cab (
                    nro_recepcion, fecha_recepcion, id_pedido, id_proveedor, id_funcionario, id_sucursal, id_deposito, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDIENTE')
=======
            cur.execute("BEGIN")

            cur.execute("""
                SELECT id_orden_compra_cab, id_proveedor, id_sucursal, id_deposito, estado
                FROM orden_compra_cab
                WHERE id_orden_compra_cab = %s
                FOR UPDATE
            """, (recepcion_dto.id_orden_compra_cab,))
            oc = cur.fetchone()
            if not oc:
                cur.execute("ROLLBACK")
                return False

            if oc[4] in ('ANULADO', 'RECIBIDA', 'CERRADA'):
                cur.execute("ROLLBACK")
                return False

            id_sucursal = recepcion_dto.id_sucursal or oc[2]
            id_deposito = recepcion_dto.id_deposito or oc[3]
            if not id_sucursal or not id_deposito:
                cur.execute("ROLLBACK")
                app.logger.error("Recepción sin sucursal/depósito definido")
                return False

            cur.execute("SELECT COALESCE(MAX(nro_recepcion), 0) + 1 FROM recepcion_cab")
            nro_recepcion = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO recepcion_cab (
                    nro_recepcion, fecha_recepcion, id_orden_compra_cab, id_pedido,
                    id_proveedor, id_funcionario, id_sucursal, id_deposito, estado
                ) VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, 'CONFIRMADO')
>>>>>>> Stashed changes
                RETURNING id_recepcion
            """, (
                recepcion_dto.nro_recepcion,
                recepcion_dto.fecha_recepcion or date.today(),
                recepcion_dto.id_orden_compra_cab,
                recepcion_dto.id_proveedor or oc[1],
                recepcion_dto.id_funcionario,
                id_sucursal,
                id_deposito
            ))
            id_recepcion = cur.fetchone()[0]

<<<<<<< Updated upstream
=======
            monto_total = 0.0
>>>>>>> Stashed changes
            for det in recepcion_dto.detalle_recepcion:
                cant_rec = min(float(det.cantidad_recibida), float(det.cantidad_pedida))
                if cant_rec <= 0:
                    continue

                cur.execute("""
                    INSERT INTO recepcion_det (
<<<<<<< Updated upstream
                        id_recepcion, id_pedido_det, item_code, descripcion, cantidad_pedida, cantidad_recibida, estado
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'PENDIENTE')
                """, (
                    id_recepcion,
                    det.id_pedido_det,   # <-- agregado
=======
                        id_recepcion, id_orden_compra_det, id_item, item_code, descripcion,
                        cantidad_pedida, cantidad_recibida, estado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'CONFIRMADO')
                """, (
                    id_recepcion,
                    det.id_orden_compra_det,
                    det.id_item,
>>>>>>> Stashed changes
                    det.item_code,
                    det.descripcion,
                    det.cantidad_pedida,
                    cant_rec
                ))

<<<<<<< Updated upstream
            con.commit()
            app.logger.info(f"Recepción {id_recepcion} insertada correctamente.")
=======
                stock_dao.incrementar(cur, id_sucursal, id_deposito, det.id_item, cant_rec)
                monto_total += cant_rec * float(det.costo_unitario or 0)

            if monto_total <= 0:
                cur.execute("ROLLBACK")
                return False

            self._actualizar_estado_orden(cur, recepcion_dto.id_orden_compra_cab)
            self._registrar_cuenta_pagar(cur, recepcion_dto.id_orden_compra_cab, monto_total)

            cur.execute("COMMIT")
            app.logger.info(f"Recepción {id_recepcion} confirmada. Stock actualizado.")
>>>>>>> Stashed changes
            return True
        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al insertar recepción: {str(e)}")
            return False
        finally:
            cur.close()
            con.close()

    def _actualizar_estado_orden(self, cur, id_orden_compra_cab: int):
        cur.execute("""
            SELECT d.id_orden_compra_det, d.cantidad,
                   COALESCE(SUM(rd.cantidad_recibida), 0)
            FROM orden_compra_det d
            LEFT JOIN recepcion_det rd ON rd.id_orden_compra_det = d.id_orden_compra_det
            LEFT JOIN recepcion_cab rc ON rc.id_recepcion = rd.id_recepcion
                AND rc.estado NOT IN ('ANULADO')
            WHERE d.id_orden_compra_cab = %s
            GROUP BY d.id_orden_compra_det, d.cantidad
        """, (id_orden_compra_cab,))
        filas = cur.fetchall()
        total = len(filas)
        completos = sum(1 for f in filas if float(f[2]) >= float(f[1]))
        nuevo_estado = 'RECIBIDA' if completos == total else 'PARCIAL'
        cur.execute("""
            UPDATE orden_compra_cab SET estado = %s WHERE id_orden_compra_cab = %s
        """, (nuevo_estado, id_orden_compra_cab))

    def _registrar_cuenta_pagar(self, cur, id_orden_compra_cab: int, monto: float):
        cur.execute("""
            SELECT id_cta_compras, monto_pendiente
            FROM cta_pagar_compras
            WHERE id_orden_compra_cab = %s
        """, (id_orden_compra_cab,))
        existente = cur.fetchone()
        vencimiento = date.today() + timedelta(days=30)

        if existente:
            cur.execute("""
                UPDATE cta_pagar_compras
                SET monto_pendiente = COALESCE(monto_pendiente, 0) + %s
                WHERE id_cta_compras = %s
            """, (monto, existente[0]))
        else:
            cur.execute("""
                INSERT INTO cta_pagar_compras
                    (id_orden_compra_cab, monto_pendiente, fecha_vencimiento,
                     monto_pagado, estado_pagado, fecha_creacion)
                VALUES (%s, %s, %s, 0, 'PENDIENTE', CURRENT_DATE)
            """, (id_orden_compra_cab, monto, vencimiento))

    def confirmar_recepcion(self, id_recepcion: int):
        return True

    def anular_recepcion(self, id_recepcion: int):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        stock_dao = StockDao()
        try:
            cur.execute("BEGIN")
            cur.execute("""
                SELECT rc.id_recepcion, rc.estado, rc.id_sucursal, rc.id_deposito, rc.id_orden_compra_cab
                FROM recepcion_cab rc WHERE rc.id_recepcion = %s FOR UPDATE
            """, (id_recepcion,))
            cab = cur.fetchone()
            if not cab or cab[1] == 'ANULADO':
                cur.execute("ROLLBACK")
                return False

            cur.execute("""
                SELECT id_item, cantidad_recibida FROM recepcion_det
                WHERE id_recepcion = %s AND cantidad_recibida > 0
            """, (id_recepcion,))
            for id_item, cant in cur.fetchall():
                if not stock_dao.decrementar(cur, cab[2], cab[3], id_item, float(cant)):
                    cur.execute("ROLLBACK")
                    app.logger.error(f"Stock insuficiente para anular recepción {id_recepcion}")
                    return False

            cur.execute("""
                UPDATE recepcion_cab SET estado = 'ANULADO' WHERE id_recepcion = %s
            """, (id_recepcion,))

            if cab[4]:
                self._actualizar_estado_orden(cur, cab[4])

            cur.execute("COMMIT")
            return True
        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al anular recepción: {str(e)}")
            return False
        finally:
            cur.close()
            con.close()
