from flask import current_app as app
from app.conexion.Conexion import Conexion
from datetime import date
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compras_dto import RecepcionDto
from app.dao.gestionar_compras.registrar_recepcion_compras.dto.recepcion_de_compra_detalle_dto import RecepcionDetalleDto

class RecepcionDao:

    # ============================================
    # Obtener pedido por número (cabecera + detalles)
    # ============================================
    def obtener_pedido_por_nro(self, nro_pedido: str):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Cabecera
            cur.execute("""
                SELECT 
                    c.id_pedido_compra_cab,
                    c.nro_pedido,
                    c.id_proveedor,
                    p.prov_nombre,
                    c.fecha_necesaria,
                    c.id_sucursal,
                    c.id_deposito
                FROM pedido_compra_cab c
                JOIN proveedor p ON p.id_proveedor = c.id_proveedor
                WHERE c.nro_pedido = %s
                LIMIT 1
            """, (nro_pedido,))
            cab = cur.fetchone()

            if not cab:
                return None

            pedido = {
                'id_pedido': cab[0],
                'nro_pedido': cab[1],
                'id_proveedor': cab[2],
                'proveedor_nombre': cab[3],
                'fecha_vencimiento': cab[4].strftime('%Y-%m-%d') if cab[4] else None,
                'id_sucursal': cab[5],
                'id_deposito': cab[6],
                'detalles': []
            }

            # Detalles
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
                })

            return pedido

        except Exception as e:
            app.logger.error(f"Error al obtener pedido por nro {nro_pedido}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    # ============================================
    # Agregar recepción
    # ============================================
    def agregar_recepcion(self, recepcion_dto: RecepcionDto):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Generar número correlativo de recepción
            cur.execute("SELECT COALESCE(MAX(nro_recepcion), 0) + 1 FROM recepcion_cab;")
            nro_recepcion = cur.fetchone()[0]

            # Insertar cabecera
            cur.execute("""
                INSERT INTO recepcion_cab (
                    nro_recepcion, fecha_recepcion, id_pedido, id_proveedor, id_funcionario, id_sucursal, id_deposito, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'CONFIRMADO')
                RETURNING id_recepcion
            """, (
                nro_recepcion,
                recepcion_dto.fecha_recepcion or date.today(),
                recepcion_dto.id_pedido,
                recepcion_dto.id_proveedor,
                recepcion_dto.id_funcionario,
                recepcion_dto.id_sucursal,
                recepcion_dto.id_deposito
            ))
            id_recepcion = cur.fetchone()[0]

            # Insertar detalles
            for det in recepcion_dto.detalle_recepcion:
                cant_rec = min(float(det.cantidad_recibida), float(det.cantidad_pedida))
                cur.execute("""
                    INSERT INTO recepcion_det (
                        id_recepcion, id_pedido_det, item_code, descripcion, cantidad_pedida, cantidad_recibida, estado
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'CONFIRMADO')
                """, (
                    id_recepcion,
                    det.id_pedido_det,
                    det.item_code,
                    det.descripcion,
                    det.cantidad_pedida,
                    cant_rec
                ))

            con.commit()
            app.logger.info(f"Recepción {id_recepcion} insertada correctamente con número {nro_recepcion}.")
            return True

        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al insertar recepción: {str(e)}")
            return False

        finally:
            cur.close()
            con.close()

    # ============================================
    # Confirmar recepción
    # ============================================
    def confirmar_recepcion(self, id_recepcion: int):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE recepcion_cab
                SET estado = 'CONFIRMADO'
                WHERE id_recepcion = %s
            """, (id_recepcion,))
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al confirmar recepción: {str(e)}")
            return False
        finally:
            cur.close()
            con.close()

    # ============================================
    # Anular recepción
    # ============================================
    def anular_recepcion(self, id_recepcion: int):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE recepcion_cab
                SET estado = 'ANULADO'
                WHERE id_recepcion = %s
            """, (id_recepcion,))
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al anular recepción: {str(e)}")
            return False
        finally:
            cur.close()
            con.close()
