# ---------------------- DAO ---------------------- 
from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compras_dto import PedidoDeComprasDto
from app.dao.gestionar_compras.registrar_pedido_compras.dto.pedido_de_compra_detalle_dto import PedidoDeCompraDetalleDto

class PedidoDeComprasDao:

    ESTADOS_VALIDOS = ('PENDIENTE', 'APROBADO', 'ANULADO')

    # ------------------------------
    # Cambiar estado (libre, mismo patrón que Solicitud/Presupuesto)
    # ------------------------------
    def cambiar_estado(self, id_pedido_compra_cab, nuevo_estado):
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            return False, f"Estado inválido. Use uno de: {', '.join(self.ESTADOS_VALIDOS)}"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(
                "UPDATE pedido_compra_cab SET estado = %s WHERE id_pedido_compra_cab = %s",
                (nuevo_estado, id_pedido_compra_cab)
            )
            if cur.rowcount == 0:
                con.rollback()
                return False, 'No existe el pedido'
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al cambiar estado de pedido {id_pedido_compra_cab}: {str(e)}")
            return False, str(e)
        finally:
            cur.close()
            con.close()

    # ------------------------------
    # Obtener datos de un presupuesto (cabecera aprobada) para precargar un pedido
    # ------------------------------
    def obtener_presupuesto_para_pedido(self, cod_presupuesto):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT pc.id_pre_compra_cab, pc.id_proveedor, prov.prov_nombre, pc.estado,
                       pc.id_sucursal, pc.id_deposito, pc.fun_id, sc.nro_solicitud, sc.fecha_necesaria
                FROM presupuesto_compra_cab pc
                LEFT JOIN proveedor prov ON prov.id_proveedor = pc.id_proveedor
                LEFT JOIN v_com_solicitud sc ON sc.id_solicitud = pc.id_solicitud
                WHERE pc.cod_presupuesto = %s
                ORDER BY pc.id_pre_compra_cab DESC
                LIMIT 1
            """, (cod_presupuesto,))
            cab = cur.fetchone()
            if not cab:
                return None

            presupuesto = {
                'id_pre_compra_cab': cab[0],
                'id_proveedor': cab[1],
                'proveedor_nombre': cab[2] or '',
                'estado': cab[3],
                'id_sucursal': cab[4],
                'id_deposito': cab[5],
                'id_funcionario': cab[6],
                'nro_solicitud': cab[7],
                'fecha_necesaria': cab[8].strftime("%Y-%m-%d") if cab[8] else None,
                'detalle': []
            }

            cur.execute("""
                SELECT d.item_code, i.descripcion, i.id_item,
                       COALESCE(i.id_proveedor, %s) AS id_proveedor,
                       d.cantidad, d.precio_unitario
                FROM presupuesto_compra_det d
                LEFT JOIN item i ON i.item_code = d.item_code
                WHERE d.id_pre_compra_cab = %s
            """, (cab[1], presupuesto['id_pre_compra_cab']))
            for f in cur.fetchall():
                presupuesto['detalle'].append({
                    'item_code': f[0],
                    'item_descripcion': f[1] or '',
                    'id_item': f[2],
                    'id_proveedor': f[3],
                    'cant_pedido': float(f[4]) if f[4] is not None else 0,
                    'costo_unitario': float(f[5]) if f[5] is not None else 0
                })
            return presupuesto
        except Exception as e:
            app.logger.error(f"Error al obtener presupuesto {cod_presupuesto} para pedido: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

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
            pdc.tipo_factura,
            COALESCE(pdc.estado,'PENDIENTE') AS estado
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
                'tipo_factura': f[9] if f[9] else '',
                'estado': f[10]
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
         id_solicitud, nro_solicitud, fecha_necesaria, id_pre_compra_cab)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                getattr(pedido_dto, 'fecha_necesaria', None),
                getattr(pedido_dto, 'id_pre_compra_cab', None)
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

    # ------------------------------
    # Edición de un pedido (solo mientras está PENDIENTE)
    # ------------------------------
    def obtener_para_editar(self, id_pedido):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT pdc.id_pedido_compra_cab, pdc.nro_pedido, pdc.fecha_pedido, pdc.fecha_necesaria,
                       pdc.id_funcionario, CONCAT(f.nombres, ' ', f.apellidos), pdc.id_sucursal, pdc.id_deposito,
                       pdc.id_proveedor, prov.prov_nombre, pdc.tipo_factura, COALESCE(pdc.estado, '')
                FROM pedido_compra_cab pdc
                LEFT JOIN funcionarios f ON f.fun_id = pdc.id_funcionario
                LEFT JOIN proveedor prov ON prov.id_proveedor = pdc.id_proveedor
                WHERE pdc.id_pedido_compra_cab = %s
            """, (id_pedido,))
            f = cur.fetchone()
            if not f:
                return None
            pedido = {
                'id_pedido': f[0], 'nro_pedido': f[1],
                'fecha_pedido': f[2].strftime("%Y-%m-%d") if f[2] else '',
                'fecha_necesaria': f[3].strftime("%Y-%m-%d") if f[3] else '',
                'id_funcionario': f[4], 'funcionario': (f[5] or '').strip(),
                'id_sucursal': f[6], 'id_deposito': f[7],
                'id_proveedor': f[8], 'proveedor': f[9] or '',
                'tipo_factura': f[10] or '', 'estado': f[11], 'detalle': []
            }
            cur.execute("""
                SELECT item_code, item_descripcion, cant_pedido, costo_unitario
                FROM pedido_compra_det WHERE id_pedido_compra_cab = %s ORDER BY id_pedido_compra_det
            """, (id_pedido,))
            pedido['detalle'] = [{'item_code': r[0], 'descripcion': r[1] or '', 'cantidad': float(r[2]),
                                  'precio': float(r[3])} for r in cur.fetchall()]
            return pedido
        finally:
            cur.close()
            con.close()

    def modificar(self, id_pedido, cabecera, detalles):
        """Actualiza cabecera y detalle. Solo se permite si el pedido está PENDIENTE.
        Devuelve (ok, mensaje_de_error)."""
        if not detalles:
            return False, 'El pedido debe tener al menos un producto.'
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute("SELECT estado, nro_pedido FROM pedido_compra_cab WHERE id_pedido_compra_cab = %s", (id_pedido,))
            f = cur.fetchone()
            if not f:
                return False, 'El pedido no existe.'
            if (f[0] or '') != 'PENDIENTE':
                return False, f'Solo se puede modificar un pedido en estado PENDIENTE (este está {f[0]}).'
            nro_pedido = f[1]

            if not cabecera.get('id_sucursal') or not cabecera.get('id_deposito') or not cabecera.get('tipo_factura'):
                return False, 'Completá sucursal, depósito y tipo de factura.'
            cur.execute("""UPDATE pedido_compra_cab
                           SET id_sucursal = %s, id_deposito = %s, tipo_factura = %s, fecha_necesaria = %s
                           WHERE id_pedido_compra_cab = %s""",
                        (cabecera['id_sucursal'], cabecera['id_deposito'], cabecera['tipo_factura'],
                         cabecera.get('fecha_necesaria') or None, id_pedido))

            # unidad de medida e impuesto de los ítems que ya estaban en el pedido
            cur.execute("""SELECT item_code, item_descripcion, unidad_med, tipo_impuesto
                           FROM pedido_compra_det WHERE id_pedido_compra_cab = %s""", (id_pedido,))
            previos = {r[0]: r for r in cur.fetchall()}
            cur.execute("DELETE FROM pedido_compra_det WHERE id_pedido_compra_cab = %s", (id_pedido,))
            vistos = set()
            for d in detalles:
                codigo = str(d.get('item_code') or '')
                cant, costo = float(d.get('cantidad') or 0), float(d.get('precio') or 0)
                if not codigo or cant <= 0 or costo <= 0:
                    con.rollback()
                    return False, 'Todos los productos deben tener cantidad y precio mayores a cero.'
                if codigo in vistos:
                    con.rollback()
                    return False, f'El producto {codigo} está repetido.'
                vistos.add(codigo)
                if codigo in previos:
                    _, descripcion, unidad, impuesto = previos[codigo]
                else:
                    cur.execute("SELECT descripcion, unidad_med, id_tipo_impuesto FROM item WHERE item_code = %s", (codigo,))
                    it = cur.fetchone()
                    if not it:
                        con.rollback()
                        return False, f'El producto {codigo} no existe.'
                    descripcion, unidad, impuesto = it
                cur.execute("""INSERT INTO pedido_compra_det
                               (id_pedido_compra_cab, nro_pedido, item_code, item_descripcion, unidad_med, cant_pedido, costo_unitario, tipo_impuesto)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                            (id_pedido, nro_pedido, codigo, descripcion, unidad, cant, costo, impuesto))
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al modificar pedido {id_pedido}: {e}")
            return False, 'No se pudo modificar el pedido.'
        finally:
            cur.close()
            con.close()
