# ---------------------- DAO ---------------------- 
from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compras_dto import PedidoDeComprasDto
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto

class PedidoDeComprasDao:

    # ------------------------------
    # Obtener todos los productos (items) con stock real y proveedor
    # ------------------------------
    def obtener_productos(self, id_sucursal=None, id_deposito=None):
        query = """
        SELECT
            i.item_code,
            i.descripcion,
            COALESCE(s.cantidad,0) AS stock,
            COALESCE(i.precio_unitario,0) AS precio_unitario,
            i.id_proveedor,
            p.prov_nombre
        FROM item i
        LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN stock s ON s.id_item = i.id_item
        """ + (" AND s.id_sucursal = %s AND s.id_deposito = %s" if id_sucursal and id_deposito else "") + """
        WHERE i.activo = TRUE
        ORDER BY i.descripcion
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            if id_sucursal and id_deposito:
                cur.execute(query, (id_sucursal, id_deposito))
            else:
                cur.execute(query)
            filas = cur.fetchall()
            productos = []
            for f in filas:
                productos.append({
                    'item_code': f[0],
                    'nombre': f[1],
                    'stock': float(f[2]),
                    'precio_unitario': float(f[3]),
                    'id_proveedor': f[4],
                    'proveedor_nombre': f[5] if f[5] else ''
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener proveedor de un item
    # ------------------------------
    def obtener_producto_por_id(self, id_item):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT i.item_code, i.descripcion, i.id_proveedor, p.prov_nombre
                FROM item i
                LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                WHERE i.item_code = %s
            """, (str(id_item),))
            fila = cur.fetchone()
            if fila:
                return {
                    'item_code': fila[0],
                    'nombre': fila[1],
                    'id_proveedor': fila[2],
                    'proveedor_nombre': fila[3] if fila[3] else ''
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener proveedor del item {id_item}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener todos los pedidos
    # ------------------------------
    def obtener_pedidos(self):
        query = """
        SELECT
            pdc.id_pedido_compra_cab,
            pdc.nro_pedido,
            pdc.fecha_pedido,
            f.fun_id,
            CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
            s.descripcion AS sucursal,
            d.descripcion AS deposito,
            pdc.id_proveedor,
            prov.prov_nombre,
            pdc.tipo_factura
        FROM pedido_compra_cab pdc
        LEFT JOIN funcionarios f ON f.fun_id = pdc.id_funcionario
        LEFT JOIN sucursal s ON s.id_sucursal = pdc.id_sucursal
        LEFT JOIN deposito d ON d.id_deposito = pdc.id_deposito AND d.activo = TRUE
        LEFT JOIN proveedor prov ON prov.id_proveedor = pdc.id_proveedor
        ORDER BY pdc.id_pedido_compra_cab DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            filas = cur.fetchall()
            return [{
                'id_pedido_compra_cab': f[0],
                'nro_pedido': f[1],
                'fecha_pedido': f[2].strftime("%Y-%m-%d") if f[2] else None,
                'fun_id': f[3],
                'funcionario': f[4],
                'sucursal': f[5],
                'deposito': f[6] if f[6] else '',
                'id_proveedor': f[7],
                'proveedor_nombre': f[8] if f[8] else '',
                'tipo_factura': f[9] if f[9] else ''
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener pedidos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener un pedido completo por ID (incluye detalle)
    # ------------------------------
    def obtener_pedido_por_id(self, id_pedido):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            # Cabecera
            cur.execute("""
                SELECT
                    pdc.id_pedido_compra_cab,
                    pdc.nro_pedido,
                    pdc.fecha_pedido,
                    f.fun_id,
                    CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
                    s.descripcion AS sucursal,
                    d.descripcion AS deposito,
                    pdc.id_proveedor,
                    prov.prov_nombre,
                    pdc.tipo_factura,
                    COALESCE(pdc.estado,'') AS estado
                FROM pedido_compra_cab pdc
                LEFT JOIN funcionarios f ON f.fun_id = pdc.id_funcionario
                LEFT JOIN sucursal s ON s.id_sucursal = pdc.id_sucursal
                LEFT JOIN deposito d ON d.id_deposito = pdc.id_deposito
                LEFT JOIN proveedor prov ON prov.id_proveedor = pdc.id_proveedor
                WHERE pdc.id_pedido_compra_cab = %s
            """, (id_pedido,))
            fila = cur.fetchone()

            if not fila:
                return None

            pedido = {
                'id_pedido_compra_cab': fila[0],
                'nro_pedido': fila[1],
                'fecha_pedido': fila[2].strftime("%Y-%m-%d") if fila[2] else None,
                'fun_id': fila[3],
                'funcionario': fila[4],
                'sucursal': fila[5],
                'deposito': fila[6] if fila[6] else '',
                'id_proveedor': fila[7],
                'proveedor_nombre': fila[8] if fila[8] else '',
                'tipo_factura': fila[9] if fila[9] else '',
                'estado': fila[10],
                'detalle': []
            }

            # Detalle
            cur.execute("""
                SELECT
                    d.id_pedido_compra_det,
                    d.item_code,
                    d.item_descripcion,
                    d.unidad_med,
                    d.cant_pedido,
                    d.costo_unitario,
                    d.tipo_impuesto
                FROM pedido_compra_det d
                WHERE d.id_pedido_compra_cab = %s
                ORDER BY d.id_pedido_compra_det
            """, (pedido['id_pedido_compra_cab'],))
            filas_detalle = cur.fetchall()
            for f in filas_detalle:
                pedido['detalle'].append({
                    'id_pedido_compra_det': f[0],
                    'item_code': f[1],
                    'item_descripcion': f[2],
                    'unidad_med': f[3],
                    'cant_pedido': float(f[4]),
                    'costo_unitario': float(f[5]),
                    'tipo_impuesto': f[6]
                })

            return pedido

        except Exception as e:
            app.logger.error(f"Error al obtener pedido ID {id_pedido}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Agregar nuevo pedido
    # ------------------------------
    def agregar(self, pedido_dto: PedidoDeComprasDto) -> bool:
        insert_cabecera = """
        INSERT INTO pedido_compra_cab
        (fecha_pedido, id_funcionario, id_sucursal, id_deposito, nro_pedido, id_proveedor, tipo_factura,
         id_solicitud, nro_solicitud, fecha_necesaria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id_pedido_compra_cab
        """
        insert_detalle = """
        INSERT INTO pedido_compra_det
        (id_pedido_compra_cab, nro_pedido, item_code, item_descripcion, unidad_med, cant_pedido, costo_unitario, tipo_impuesto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        conexion = Conexion()
        con = conexion.getConexion()
        con.autocommit = False
        cur = con.cursor()
        try:
            nro_pedido = pedido_dto.nro_pedido
            parametros_cabecera = (
                pedido_dto.fecha_pedido,
                pedido_dto.id_funcionario,
                pedido_dto.id_sucursal,
                pedido_dto.id_deposito,
                nro_pedido,
                pedido_dto.id_proveedor,
                pedido_dto.tipo_factura,
                getattr(pedido_dto, 'id_solicitud', None),
                getattr(pedido_dto, 'nro_solicitud', None),
                getattr(pedido_dto, 'fecha_necesaria', None)
            )
            cur.execute(insert_cabecera, parametros_cabecera)
            id_pedido_cab = cur.fetchone()[0]

            for det in pedido_dto.detalle_pedido:
                cur.execute(insert_detalle, (
                    id_pedido_cab,
                    nro_pedido,
                    det.item_code,
                    det.item_descripcion,
                    det.unidad_med,
                    det.cant_pedido,
                    det.costo_unitario,
                    det.tipo_impuesto
                ))

            con.commit()
            return True
        except Exception as e:
            app.logger.error(f"Error al agregar pedido: {str(e)}")
            con.rollback()
            return False
        finally:
            con.autocommit = True
            cur.close()
            con.close()

    # ------------------------------
    # Anular pedido
    # ------------------------------
    def anular(self, id_pedido_compra_cab: int) -> bool:
        sql = "UPDATE pedido_compra_cab SET estado='ANULADO' WHERE id_pedido_compra_cab=%s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_pedido_compra_cab,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al anular pedido: {str(e)}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener siguiente número de pedido
    # ------------------------------
    def obtener_siguiente_nro_pedido(self):
        query = "SELECT COALESCE(MAX(id_pedido_compra_cab), 0) + 1 FROM pedido_compra_cab"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(query)
            fila = cur.fetchone()
            return fila[0] if fila else 1
        except Exception as e:
            app.logger.error(f"Error al obtener siguiente nro_pedido: {str(e)}")
            return 1
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener datos de una solicitud específica por NRO
    # ------------------------------
    def obtener_solicitud_por_nro(self, nro_solicitud):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            query_cabecera = """
            SELECT
                sc.id_solicitud,
                sc.nro_solicitud,
                sc.id_solicitante,
                CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
                sc.id_sucursal,
                s.descripcion AS sucursal,
                sc.id_deposito,
                d.descripcion AS deposito,
                sc.fecha_solicitud
            FROM solicitud_compra_cab sc
            LEFT JOIN funcionarios f ON f.fun_id = sc.id_solicitante
            LEFT JOIN sucursal s ON s.id_sucursal = sc.id_sucursal
            LEFT JOIN deposito d ON d.id_deposito = sc.id_deposito
            WHERE sc.nro_solicitud = %s
            """
            cur.execute(query_cabecera, (nro_solicitud,))
            fila = cur.fetchone()
            if not fila:
                return None

            solicitud = {
                'id_solicitud': fila[0],
                'nro_solicitud': fila[1],
                'id_funcionario': fila[2],
                'funcionario': fila[3],
                'id_sucursal': fila[4],
                'sucursal': fila[5],
                'id_deposito': fila[6],
                'deposito': fila[7],
                'fecha_solicitud': fila[8].strftime("%Y-%m-%d") if fila[8] else None,
                'detalle': []
            }

            query_detalle = """
            SELECT
                i.item_code,
                i.descripcion AS item_descripcion,
                sd.cantidad,
                COALESCE(i.precio_unitario,0) AS precio_unitario,
                COALESCE(st.cantidad,0) AS stock,
                i.id_proveedor,
                p.prov_nombre
            FROM solicitud_compra_det sd
            LEFT JOIN item i ON i.id_item = sd.id_item
            LEFT JOIN stock st ON st.id_item = i.id_item AND st.id_sucursal = %s AND st.id_deposito = %s
            LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
            WHERE sd.id_solicitud = %s
            """
            cur.execute(query_detalle, (solicitud['id_sucursal'], solicitud['id_deposito'], solicitud['id_solicitud']))
            filas_detalle = cur.fetchall()
            for f in filas_detalle:
                solicitud['detalle'].append({
                    'item_code': f[0],
                    'item_descripcion': f[1],
                    'cant_pedido': float(f[2]),
                    'costo_unitario': float(f[3]),
                    'stock': float(f[4]),
                    'id_proveedor': f[5],
                    'proveedor': f[6] if f[6] else ''
                })

            return solicitud
        except Exception as e:
            app.logger.error(f"Error al obtener solicitud nro {nro_solicitud}: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()
