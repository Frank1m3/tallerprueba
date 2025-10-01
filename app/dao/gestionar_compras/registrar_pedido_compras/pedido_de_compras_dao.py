from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compras_dto import PedidoDeComprasDto
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto

class PedidoDeComprasDao:

    # ================================
    # Obtener todos los productos (items) con stock real y proveedor
    # ================================
    def obtener_productos(self, id_sucursal=None, id_deposito=None):
        query = """
        SELECT
            i.id_item,
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
                    'id_item': f[0],
                    'item_code': f[1],
                    'nombre': f[2],
                    'stock': float(f[3]),
                    'precio_unitario': float(f[4]),
                    'id_proveedor': f[5],
                    'proveedor_nombre': f[6] if f[6] else ''
                })
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener todos los pedidos
    # ================================
    def obtener_pedidos(self):
        query = """
        SELECT
            pdc.id_pedido_compra_cab,
            pdc.nro_pedido,
            pdc.fecha_pedido,
            f.fun_id,
            CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
            s.descripcion AS sucursal,
            d.descripcion AS deposito
        FROM pedido_compra_cab pdc
        LEFT JOIN funcionarios f ON f.fun_id = pdc.id_funcionario
        LEFT JOIN sucursal s ON s.id_sucursal = pdc.id_sucursal
        LEFT JOIN deposito d ON d.id_deposito = pdc.id_deposito AND d.activo = TRUE
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
                'deposito': f[6] if f[6] else ''
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener pedidos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Agregar nuevo pedido
    # ================================
    def agregar(self, pedido_dto: PedidoDeComprasDto) -> bool:
        if pedido_dto.id_proveedor is None:
            app.logger.error("No se puede insertar pedido: id_proveedor es None")
            return False

        insert_cabecera = """
        INSERT INTO pedido_compra_cab
        (fecha_pedido, id_funcionario, id_sucursal, id_deposito, id_proveedor)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_pedido_compra_cab, nro_pedido
        """

        insert_detalle = """
        INSERT INTO pedido_compra_det
        (id_pedido_compra_cab, nro_pedido, id_item, item_descripcion, unidad_med, cant_pedido, costo_unitario, tipo_impuesto, id_proveedor)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        conexion = Conexion()
        con = conexion.getConexion()
        con.autocommit = False
        cur = con.cursor()
        try:
            # Insertar cabecera
            parametros_cabecera = (
                pedido_dto.fecha_pedido,
                pedido_dto.id_funcionario,
                pedido_dto.id_sucursal,
                pedido_dto.id_deposito,
                pedido_dto.id_proveedor
            )
            app.logger.info(f"Inserting pedido_cab: {parametros_cabecera}")
            cur.execute(insert_cabecera, parametros_cabecera)
            fila = cur.fetchone()
            id_pedido_cab = fila[0]
            nro_pedido = fila[1]

            # Insertar detalles
            for det in pedido_dto.detalle_pedido:
                if det.id_item is None:
                    raise ValueError("id_item no puede ser None")
                cur.execute(insert_detalle, (
                    id_pedido_cab,
                    nro_pedido,
                    det.id_item,
                    det.item_descripcion,
                    det.unidad_med,
                    det.cant_pedido,
                    det.costo_unitario,
                    det.tipo_impuesto,
                    det.id_proveedor or pedido_dto.id_proveedor
                ))

            con.commit()
            app.logger.info(f"Pedido {nro_pedido} agregado correctamente con id_proveedor {pedido_dto.id_proveedor}")
            return True
        except Exception as e:
            app.logger.error(f"Error al agregar pedido: {str(e)}")
            con.rollback()
            return False
        finally:
            con.autocommit = True
            cur.close()
            con.close()

    # ================================
    # Anular pedido
    # ================================
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

    # ================================
    # Obtener siguiente número de pedido
    # ================================
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
