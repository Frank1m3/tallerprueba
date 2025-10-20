from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compras_dto import SolicitudDto
from app.dao.gestionar_compras.registrar_solicitud_compras.dto.solicitud_de_compra_detalle_dto import SolicitudDetalleDto

class SolicitudCompraDao:

    # ================================
    # Obtener todas las solicitudes (para index)
    # ================================
    def obtener_solicitudes(self):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT 
                    sc.id_solicitud,
                    sc.nro_solicitud,
                    sc.fecha_solicitud,
                    f.nombres || ' ' || f.apellidos AS funcionario_nombre,
                    s.descripcion AS sucursal_nombre,
                    d.descripcion AS deposito_nombre,
                    p.prov_nombre AS proveedor_nombre,
                    sc.estado
                FROM solicitud_compra_cab sc
                LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
                LEFT JOIN sucursal s ON s.id_sucursal = sc.id_sucursal
                LEFT JOIN deposito d ON d.id_deposito = sc.id_deposito AND d.activo = TRUE
                LEFT JOIN proveedor p ON p.id_proveedor = sc.id_proveedor
                ORDER BY sc.nro_solicitud DESC
            """)
            filas = cur.fetchall()
            solicitudes = []
            for f in filas:
                solicitudes.append({
                    'id_solicitud': f[0],
                    'nro_solicitud': f[1],
                    'solicitante': f[3] or '',
                    'sucursal': f[4] or '',
                    'deposito': f[5] or '',
                    'fecha_solicitud': f[2].strftime("%Y-%m-%d") if f[2] else None,
                    'proveedor_nombre': f[6] or '',
                    'estado': f[7]
                })
            return solicitudes
        except Exception as e:
            app.logger.error(f"Error al obtener solicitudes: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener productos (opcional filtro por sucursal, depósito y proveedor)
    # ================================
    def obtener_productos(self, id_sucursal=None, id_deposito=None, id_proveedor=None):
        query = """
        SELECT 
            i.id_item,
            i.item_code,
            i.descripcion AS nombre_producto,
            COALESCE(s.cantidad,0) AS stock,
            COALESCE(i.precio_unitario,0) AS precio,
            i.id_proveedor,
            p.prov_nombre AS proveedor_nombre
        FROM item i
        LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN stock s ON s.id_item = i.id_item
        WHERE i.activo = TRUE
        """
        params = []
        if id_sucursal and id_deposito:
            query += " AND s.id_sucursal = %s AND s.id_deposito = %s"
            params.extend([id_sucursal, id_deposito])
        if id_proveedor:
            query += " AND i.id_proveedor = %s"
            params.append(id_proveedor)
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
                    'nombre_producto': f[2] or '',
                    'stock': float(f[3]),
                    'precio': float(f[4]),
                    'id_proveedor': f[5],
                    'proveedor_nombre': f[6] or '',
                    'unidad_med': 1
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener solicitud por ID
    # ================================
    def obtener_solicitud_por_id(self, id_solicitud):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Cabecera
            cur.execute("""
                SELECT 
                    sc.id_solicitud,
                    sc.nro_solicitud,
                    sc.fecha_solicitud,
                    sc.id_solicitante,
                    f.nombres || ' ' || f.apellidos AS funcionario_nombre,
                    sc.id_sucursal,
                    s.descripcion AS sucursal_nombre,
                    sc.id_deposito,
                    d.descripcion AS deposito_nombre,
                    sc.id_proveedor,
                    p.prov_nombre AS proveedor_nombre,
                    sc.estado
                FROM solicitud_compra_cab sc
                LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
                LEFT JOIN sucursal s ON s.id_sucursal = sc.id_sucursal
                LEFT JOIN deposito d ON d.id_deposito = sc.id_deposito AND d.activo = TRUE
                LEFT JOIN proveedor p ON p.id_proveedor = sc.id_proveedor
                WHERE sc.id_solicitud = %s
            """, (id_solicitud,))
            cab = cur.fetchone()
            if not cab:
                return None

            solicitud = {
                'id_solicitud': cab[0],
                'nro_solicitud': cab[1],
                'fecha_solicitud': cab[2].strftime("%Y-%m-%d") if cab[2] else None,
                'id_solicitante': cab[3],
                'funcionario_nombre': cab[4] or '',
                'id_sucursal': cab[5],
                'sucursal_nombre': cab[6] or '',
                'id_deposito': cab[7],
                'deposito_nombre': cab[8] or '',
                'id_proveedor': cab[9],
                'proveedor_nombre': cab[10] or '',
                'estado': cab[11],
                'detalles': [],
                'depositos': []
            }

            # Detalles
            cur.execute("""
                SELECT d.id_item, i.descripcion AS nombre_producto, d.unidad_medida, d.cantidad
                FROM solicitud_compra_det d
                LEFT JOIN item i ON i.id_item = d.id_item
                WHERE d.id_solicitud = %s
            """, (id_solicitud,))
            filas_det = cur.fetchall()
            for f in filas_det:
                solicitud['detalles'].append({
                    'id_item': f[0],
                    'nombre_producto': f[1] or '',
                    'unidad_med': f[2],
                    'cantidad': float(f[3])
                })

            # Depósitos de la sucursal
            cur.execute("""
                SELECT id_deposito, descripcion
                FROM deposito
                WHERE id_sucursal = %s AND activo = TRUE
            """, (solicitud['id_sucursal'],))
            filas_dep = cur.fetchall()
            for d in filas_dep:
                solicitud['depositos'].append({
                    'id_deposito': d[0],
                    'nombre_deposito': d[1]
                })

            return solicitud

        except Exception as e:
            app.logger.error(f"Error al obtener solicitud por id: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Modificar solicitud (cabecera + detalles)
    # ================================
    def modificar_solicitud(self, id_solicitud, detalles, cabecera=None):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Verificar si existe la solicitud
            cur.execute("SELECT id_solicitud FROM solicitud_compra_cab WHERE id_solicitud = %s", (id_solicitud,))
            if not cur.fetchone():
                return False

            # Actualizar cabecera si se envía
            if cabecera:
                cur.execute("""
                    UPDATE solicitud_compra_cab
                    SET id_proveedor=%s, id_sucursal=%s, id_deposito=%s, fecha_solicitud=%s
                    WHERE id_solicitud=%s
                """, (
                    cabecera.get('id_proveedor'),
                    cabecera.get('id_sucursal'),
                    cabecera.get('id_deposito'),
                    cabecera.get('fecha_solicitud'),
                    id_solicitud
                ))

            # Eliminar detalles actuales
            cur.execute("DELETE FROM solicitud_compra_det WHERE id_solicitud = %s", (id_solicitud,))

            # Insertar nuevos detalles
            for det in detalles:
                cur.execute("""
                    INSERT INTO solicitud_compra_det (id_solicitud, id_item, cantidad)
                    VALUES (%s, %s, %s)
                """, (id_solicitud, det.id_item, det.cant_solicitada))

            con.commit()
            return True
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al modificar solicitud: {str(e)}")
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

    # ================================
    # Agregar nueva solicitud (cabecera + detalles)
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
    # Anular solicitud (cambiar estado a 'ANULADO')
    # ================================
    def anular(self, id_solicitud):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Verificar si existe y está pendiente
            cur.execute("SELECT estado FROM solicitud_compra_cab WHERE id_solicitud = %s", (id_solicitud,))
            fila = cur.fetchone()
            if not fila:
                return False  # No existe
            if fila[0] != 'PENDIENTE':
                return False  # Solo se pueden anular solicitudes pendientes

            # Actualizar estado a 'ANULADO'
            cur.execute("UPDATE solicitud_compra_cab SET estado = 'ANULADO' WHERE id_solicitud = %s", (id_solicitud,))
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al anular solicitud: {str(e)}")
            return False
        finally:
            cur.close()
            con.close()    

    # ================================
    # NUEVOS MÉTODOS PARA PRESUPUESTO
    # ================================
    def obtener_solicitud_por_nro(self, nro_solicitud):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Cabecera con proveedor y funcionario
            cur.execute("""
                SELECT sc.id_solicitud, sc.nro_solicitud, sc.fecha_solicitud,
                       sc.id_proveedor, p.prov_nombre AS proveedor_nombre,
                       sc.id_solicitante, f.nombres || ' ' || f.apellidos AS funcionario_nombre
                FROM solicitud_compra_cab sc
                LEFT JOIN proveedor p ON p.id_proveedor = sc.id_proveedor
                LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
                WHERE sc.nro_solicitud = %s
            """, (nro_solicitud,))
            cab = cur.fetchone()
            if not cab:
                return None

            solicitud = {
                'id_solicitud': cab[0],
                'nro_solicitud': cab[1],
                'fecha_solicitud': cab[2].strftime("%Y-%m-%d") if cab[2] else None,
                'id_proveedor': cab[3],
                'proveedor_nombre': cab[4] or '',
                'id_funcionario': cab[5],
                'funcionario_nombre': cab[6] or '',
                'detalles': []
            }

            # Detalle de la solicitud
            detalles = self.obtener_detalle_por_numero(cab[0])
            for d in detalles:
                d['proveedor'] = solicitud['proveedor_nombre']
                d['funcionario'] = solicitud['funcionario_nombre']
            solicitud['detalles'] = detalles

            return solicitud
        except Exception as e:
            app.logger.error(f"Error al obtener solicitud {nro_solicitud}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    def obtener_detalle_por_numero(self, id_solicitud):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT d.id_item, i.descripcion AS nombre_producto, d.cantidad, d.unidad_medida
                FROM solicitud_compra_det d
                LEFT JOIN item i ON i.id_item = d.id_item
                WHERE d.id_solicitud = %s
            """, (id_solicitud,))
            detalles = []
            for fila in cur.fetchall():
                detalles.append({
                    'id_item': fila[0],
                    'nombre_producto': fila[1] or '',
                    'cantidad': float(fila[2]),
                    'unidad_med': fila[3]
                })
            return detalles
        except Exception as e:
            app.logger.error(f"Error al obtener detalle de solicitud {id_solicitud}: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()
