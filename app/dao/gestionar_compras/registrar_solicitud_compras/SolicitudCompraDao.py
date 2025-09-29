from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

class SolicitudCompraDao:

    def __init__(self):
        # Usamos la conexión de tu clase Conexion
        self.conn = Conexion().getConexion()

    # ================================
    # Obtener productos (items) con stock por sucursal y depósito
    # ================================
    def obtener_productos(self, id_sucursal=None, id_deposito=None):
        query = """
        SELECT
            i.id_item,
            i.item_code,
            i.descripcion
        FROM item i
        WHERE i.activo = TRUE
        ORDER BY i.descripcion
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            filas = cur.fetchall()
            productos = []
            for f in filas:
                productos.append({
                    'id_item': f[0],
                    'codigo': f[1],
                    'nombre': f[2]
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener depósitos por sucursal
    # ================================
    def obtener_depositos_por_sucursal(self, id_sucursal):
        query = """
        SELECT id_deposito, descripcion
        FROM deposito
        WHERE id_sucursal = %s AND activo = TRUE
        ORDER BY descripcion
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(query, (id_sucursal,))
            filas = cur.fetchall()
            return [{'id_deposito': f[0], 'nombre_deposito': f[1]} for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener depósitos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener todas las solicitudes
    # ================================
    def obtener_solicitudes(self):
        query = """
        SELECT
            sc.id_solicitud,
            sc.nro_solicitud,
            sc.fecha_solicitud,
            s.descripcion AS sucursal,
            d.descripcion AS deposito,
            CONCAT(f.nombres,' ',f.apellidos) AS solicitante,
            sc.estado
        FROM solicitud_compra_cab sc
        LEFT JOIN sucursal s ON s.id_sucursal = sc.id_sucursal
        LEFT JOIN deposito d ON d.id_deposito = sc.id_deposito AND d.activo = TRUE
        LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
        ORDER BY sc.id_solicitud DESC
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            filas = cur.fetchall()
            return [{
                'id_solicitud': f[0],
                'nro_solicitud': f[1],
                'fecha_solicitud': f[2].strftime("%Y-%m-%d") if f[2] else None,
                'sucursal': f[3],
                'deposito': f[4] if f[4] else '',
                'solicitante': f[5],
                'estado': f[6]
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener solicitudes: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Agregar nueva solicitud
    # ================================
    def agregar(self, solicitud_dto: SolicitudDto) -> bool:
        insert_cabecera = """
        INSERT INTO solicitud_compra_cab
        (nro_solicitud, fecha_solicitud, id_sucursal, id_deposito, id_solicitante, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_solicitud
        """
        insert_detalle = """
        INSERT INTO solicitud_compra_det
        (id_solicitud, id_item, cantidad, unidad_medida)
        VALUES (%s, %s, %s, %s)
        """
        con = Conexion().getConexion()
        con.autocommit = False
        cur = con.cursor()
        try:
            # Obtener siguiente nro_solicitud
            nro_solicitud = self.obtener_siguiente_nro_solicitud()

            parametros_cabecera = (
                nro_solicitud,
                solicitud_dto.fecha_solicitud,
                solicitud_dto.id_sucursal,
                solicitud_dto.id_deposito,
                solicitud_dto.id_funcionario,
                'PENDIENTE'
            )
            cur.execute(insert_cabecera, parametros_cabecera)
            id_solicitud = cur.fetchone()[0]

            for det in solicitud_dto.detalle_solicitud:
                cur.execute(insert_detalle, (
                    id_solicitud,
                    det.id_item,
                    det.cant_solicitada,
                    det.unidad_med
                ))

            con.commit()
            return True
        except Exception as e:
            app.logger.error(f"Error al agregar solicitud: {str(e)}")
            con.rollback()
            return False
        finally:
            con.autocommit = True
            cur.close()
            con.close()

    # ================================
    # Anular solicitud
    # ================================
    def anular(self, id_solicitud: int) -> bool:
        sql = "UPDATE solicitud_compra_cab SET estado='ANULADA' WHERE id_solicitud=%s"
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_solicitud,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al anular solicitud: {str(e)}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ================================
    # NUEVO MÉTODO: obtener siguiente nro de solicitud
    # ================================
    def obtener_siguiente_nro_solicitud(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(nro_solicitud), 0) + 1 AS siguiente FROM solicitud_compra_cab;")
                row = cur.fetchone()
                return row[0] if row else 1
        except Exception as e:
            app.logger.error(f"Error al obtener siguiente nro_solicitud: {e}")
            return 1
