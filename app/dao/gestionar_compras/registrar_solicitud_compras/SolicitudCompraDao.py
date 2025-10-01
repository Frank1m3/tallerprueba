from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

class SolicitudCompraDao:

    # ================================
    # Obtener productos activos
    # ================================
    def obtener_productos(self, id_sucursal=None, id_deposito=None):
        query = """
        SELECT
            i.id_item,
            i.item_code,
            i.descripcion,
            COALESCE(s.cantidad,0) AS stock,
            COALESCE(i.precio_unitario,0) AS precio,
            i.id_proveedor,
            p.prov_nombre,
            'PENDIENTE' AS estado
        FROM item i
        LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN stock s ON s.id_item = i.id_item
        WHERE i.activo = TRUE
        """
        params = []
        if id_sucursal and id_deposito:
            query += " AND s.id_sucursal = %s AND s.id_deposito = %s"
            params.extend([id_sucursal, id_deposito])
        query += " ORDER BY i.descripcion"

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query, params)
            filas = cur.fetchall()
            productos = []
            for f in filas:
                productos.append({
                    'id_item': f[0],
                    'item_code': f[1],
                    'nombre': f[2],
                    'stock': float(f[3]),
                    'precio': float(f[4]),
                    'id_proveedor': f[5],
                    'proveedor_nombre': f[6] or '',
                    'unidad_med': 1,
                    'estado': f[7]
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener productos filtrando por proveedor
    # ================================
    def obtener_productos_por_proveedor(self, id_proveedor, id_sucursal=None, id_deposito=None):
        query = """
        SELECT
            i.id_item,
            i.item_code,
            i.descripcion,
            COALESCE(s.cantidad,0) AS stock,
            COALESCE(i.precio_unitario,0) AS precio,
            'PENDIENTE' AS estado
        FROM item i
        LEFT JOIN stock s ON s.id_item = i.id_item
        WHERE i.activo = TRUE AND i.id_proveedor = %s
        """
        params = [id_proveedor]
        if id_sucursal and id_deposito:
            query += " AND s.id_sucursal = %s AND s.id_deposito = %s"
            params.extend([id_sucursal, id_deposito])
        query += " ORDER BY i.descripcion"

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query, params)
            filas = cur.fetchall()
            productos = []
            for f in filas:
                productos.append({
                    'id_item': f[0],
                    'item_code': f[1],
                    'nombre': f[2],
                    'stock': float(f[3]),
                    'precio': float(f[4]),
                    'unidad_med': 1,
                    'estado': f[5]
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos por proveedor: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener depósitos de sucursal
    # ================================
    def obtener_depositos_por_sucursal(self, id_sucursal):
        query = """
        SELECT id_deposito, descripcion
        FROM deposito
        WHERE id_sucursal = %s AND activo = TRUE
        ORDER BY descripcion
        """
        conexion = Conexion()
        con = conexion.getConexion()
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
            f.fun_id,
            CONCAT(f.nombres,' ',f.apellidos) AS solicitante,
            s.descripcion AS sucursal,
            d.descripcion AS deposito,
            p.prov_nombre AS proveedor,
            sc.estado
        FROM solicitud_compra_cab sc
        LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
        LEFT JOIN sucursal s ON s.id_sucursal = sc.id_sucursal
        LEFT JOIN deposito d ON d.id_deposito = sc.id_deposito AND d.activo = TRUE
        LEFT JOIN proveedor p ON p.id_proveedor = sc.id_proveedor
        ORDER BY sc.id_solicitud DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            filas = cur.fetchall()
            return [dict(
                id_solicitud=f[0],
                nro_solicitud=f[1],
                fecha_solicitud=f[2].strftime("%Y-%m-%d") if f[2] else None,
                fun_id=f[3],
                solicitante=f[4],
                sucursal=f[5],
                deposito=f[6] or '',
                proveedor=f[7] or '',
                estado=f[8]
            ) for f in filas]
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
        (fecha_solicitud, id_solicitante, id_sucursal, id_deposito, id_proveedor, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_solicitud
        """
        insert_detalle = """
        INSERT INTO solicitud_compra_det
        (id_solicitud, id_item, cantidad, unidad_medida)
        VALUES (%s, %s, %s, %s)
        """
        conexion = Conexion()
        con = conexion.getConexion()
        con.autocommit = False
        cur = con.cursor()
        try:
            # Cabecera
            cur.execute(insert_cabecera, (
                solicitud_dto.fecha_solicitud,
                solicitud_dto.id_funcionario,
                solicitud_dto.id_sucursal,
                solicitud_dto.id_deposito,
                solicitud_dto.id_proveedor,
                'PENDIENTE'
            ))
            id_solicitud = cur.fetchone()[0]

            # Detalle
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
        conexion = Conexion()
        con = conexion.getConexion()
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
    # Obtener siguiente número de solicitud
    # ================================
    def obtener_siguiente_nro_solicitud(self):
        query = "SELECT COALESCE(MAX(nro_solicitud), 0) + 1 FROM solicitud_compra_cab"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            fila = cur.fetchone()
            return fila[0] if fila else 1
        except Exception as e:
            app.logger.error(f"Error al obtener siguiente nro_solicitud: {str(e)}")
            return 1
        finally:
            cur.close()
            con.close()
