# ---------------------- DAO ----------------------
from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_orden_compras.dto.orden_de_compras_dto import OrdenDeComprasDto
from app.dao.gestionar_compras.registrar_orden_compras.dto.orden_de_compra_detalle_dto import OrdenDeCompraDetalleDto


class OrdenDeComprasDao:

    # ------------------------------
    # Productos (items) con proveedor y stock.
    # OJO: la OC trabaja con id_item (integer), no con item_code.
    # ------------------------------
    def obtener_productos(self):
        query = """
        SELECT
            i.id_item,
            i.item_code,
            i.descripcion,
            COALESCE(i.precio_unitario,0) AS precio_unitario,
            i.id_proveedor,
            p.prov_nombre,
            COALESCE(SUM(s.cantidad),0) AS stock
        FROM item i
        LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN stock s ON s.id_item = i.id_item
        WHERE i.activo = TRUE
        GROUP BY i.id_item, i.item_code, i.descripcion, i.precio_unitario, i.id_proveedor, p.prov_nombre
        ORDER BY i.descripcion
        """
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(query)
            return [{
                'id_item': f[0],
                'item_code': f[1],
                'nombre': f[2],
                'precio_unitario': float(f[3]),
                'id_proveedor': f[4],
                'proveedor_nombre': f[5] if f[5] else '',
                'stock': float(f[6])
            } for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener productos OC: {str(e)}")
            return []
        finally:
            cur.close(); con.close()

    # ------------------------------
    # Listado de órdenes de compra
    # ------------------------------
    def obtener_ordenes(self):
        query = """
        SELECT
            oc.id_orden_compra_cab,
            oc.fecha_emision,
            oc.fun_id,
            CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
            s.descripcion AS sucursal,
            oc.id_proveedor,
            prov.prov_nombre,
            oc.id_pre_compra_cab,
            COALESCE(oc.estado,'') AS estado
        FROM orden_compra_cab oc
        LEFT JOIN funcionarios f ON f.fun_id = oc.fun_id
        LEFT JOIN sucursal s ON s.id_sucursal = oc.id_sucursal
        LEFT JOIN proveedor prov ON prov.id_proveedor = oc.id_proveedor
        ORDER BY oc.id_orden_compra_cab DESC
        """
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(query)
            return [{
                'id_orden_compra_cab': f[0],
                'fecha_emision': f[1].strftime("%Y-%m-%d") if f[1] else None,
                'fun_id': f[2],
                'funcionario': f[3],
                'sucursal': f[4],
                'id_proveedor': f[5],
                'proveedor_nombre': f[6] if f[6] else '',
                'id_pre_compra_cab': f[7],
                'estado': f[8]
            } for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener órdenes: {str(e)}")
            return []
        finally:
            cur.close(); con.close()

    # ------------------------------
    # Una OC completa por ID (con detalle)
    # ------------------------------
    def obtener_orden_por_id(self, id_orden):
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT
                    oc.id_orden_compra_cab,
                    oc.fecha_emision,
                    oc.fun_id,
                    CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
                    oc.id_sucursal,
                    s.descripcion AS sucursal,
                    oc.id_proveedor,
                    prov.prov_nombre,
                    oc.id_pre_compra_cab,
                    COALESCE(oc.estado,'') AS estado
                FROM orden_compra_cab oc
                LEFT JOIN funcionarios f ON f.fun_id = oc.fun_id
                LEFT JOIN sucursal s ON s.id_sucursal = oc.id_sucursal
                LEFT JOIN proveedor prov ON prov.id_proveedor = oc.id_proveedor
                WHERE oc.id_orden_compra_cab = %s
            """, (id_orden,))
            fila = cur.fetchone()
            if not fila:
                return None

            orden = {
                'id_orden_compra_cab': fila[0],
                'fecha_emision': fila[1].strftime("%Y-%m-%d") if fila[1] else None,
                'fun_id': fila[2],
                'funcionario': fila[3],
                'id_sucursal': fila[4],
                'sucursal': fila[5],
                'id_proveedor': fila[6],
                'proveedor_nombre': fila[7] if fila[7] else '',
                'id_pre_compra_cab': fila[8],
                'estado': fila[9],
                'detalle': []
            }

            cur.execute("""
                SELECT d.id_orden_compra_det, d.id_item, i.item_code, i.descripcion,
                       d.cantidad, d.precio_unitario, p.prov_nombre
                FROM orden_compra_det d
                LEFT JOIN item i ON i.id_item = d.id_item
                LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                WHERE d.id_orden_compra_cab = %s
                ORDER BY d.id_orden_compra_det
            """, (id_orden,))
            for f in cur.fetchall():
                orden['detalle'].append({
                    'id_orden_compra_det': f[0],
                    'id_item': f[1],
                    'item_code': f[2],
                    'item_descripcion': f[3],
                    'cantidad': float(f[4]) if f[4] is not None else 0,
                    'precio_unitario': float(f[5]) if f[5] is not None else 0,
                    'proveedor': f[6] if f[6] else ''
                })
            return orden
        except Exception as e:
            app.logger.error(f"Error al obtener orden ID {id_orden}: {str(e)}")
            return None
        finally:
            cur.close(); con.close()

    # ------------------------------
    # Agregar OC (cabecera + detalle) en una transacción
    # ------------------------------
    def agregar(self, dto: OrdenDeComprasDto) -> int:
        insert_cab = """
        INSERT INTO orden_compra_cab
        (id_pre_compra_cab, id_sucursal, fun_id, fecha_emision, id_proveedor, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_orden_compra_cab
        """
        insert_det = """
        INSERT INTO orden_compra_det
        (id_orden_compra_cab, id_item, cantidad, precio_unitario)
        VALUES (%s, %s, %s, %s)
        """
        conexion = Conexion(); con = conexion.getConexion()
        con.autocommit = False
        cur = con.cursor()
        try:
            cur.execute(insert_cab, (
                dto.id_pre_compra_cab,
                dto.id_sucursal,
                dto.fun_id,
                dto.fecha_emision,
                dto.id_proveedor,
                dto.estado
            ))
            id_cab = cur.fetchone()[0]

            for det in dto.detalle_orden:
                cur.execute(insert_det, (
                    id_cab,
                    det.id_item,
                    det.cantidad,
                    det.precio_unitario
                ))

            con.commit()
            return id_cab
        except Exception as e:
            app.logger.error(f"Error al agregar orden: {str(e)}")
            con.rollback()
            return 0
        finally:
            con.autocommit = True
            cur.close(); con.close()

    # ------------------------------
    # Anular OC
    # ------------------------------
    def anular(self, id_orden_compra_cab: int) -> bool:
        sql = "UPDATE orden_compra_cab SET estado='ANULADO' WHERE id_orden_compra_cab=%s"
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute(sql, (id_orden_compra_cab,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al anular orden: {str(e)}")
            con.rollback()
            return False
        finally:
            cur.close(); con.close()

    # ------------------------------
    # Cargar un PRESUPUESTO por su código, para prellenar la OC.
    # Mapea item_code -> id_item para que el detalle quede listo para la OC.
    # ------------------------------
    def obtener_presupuesto_por_cod(self, cod_presupuesto):
        conexion = Conexion(); con = conexion.getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT pc.id_pre_compra_cab, pc.cod_presupuesto, pc.fun_id,
                       CONCAT(f.nombres,' ',f.apellidos) AS funcionario,
                       pc.id_proveedor, prov.prov_nombre, pc.fecha_emision
                FROM presupuesto_compra_cab pc
                LEFT JOIN funcionarios f ON f.fun_id = pc.fun_id
                LEFT JOIN proveedor prov ON prov.id_proveedor = pc.id_proveedor
                WHERE pc.cod_presupuesto = %s
            """, (str(cod_presupuesto),))
            fila = cur.fetchone()
            if not fila:
                return None

            presu = {
                'id_pre_compra_cab': fila[0],
                'cod_presupuesto': fila[1],
                'fun_id': fila[2],
                'funcionario': fila[3],
                'id_proveedor': fila[4],
                'proveedor_nombre': fila[5] if fila[5] else '',
                'fecha_emision': fila[6].strftime("%Y-%m-%d") if fila[6] else None,
                'detalle': []
            }

            cur.execute("""
                SELECT i.id_item, pd.item_code, i.descripcion,
                       pd.cantidad, pd.precio_unitario,
                       i.id_proveedor, p.prov_nombre
                FROM presupuesto_compra_det pd
                LEFT JOIN item i ON i.item_code = pd.item_code
                LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
                WHERE pd.id_pre_compra_cab = %s
            """, (presu['id_pre_compra_cab'],))
            for f in cur.fetchall():
                presu['detalle'].append({
                    'id_item': f[0],
                    'item_code': f[1],
                    'item_descripcion': f[2] if f[2] else f[1],
                    'cantidad': float(f[3]) if f[3] is not None else 0,
                    'precio_unitario': float(f[4]) if f[4] is not None else 0,
                    'id_proveedor': f[5],
                    'proveedor': f[6] if f[6] else ''
                })
            return presu
        except Exception as e:
            app.logger.error(f"Error al obtener presupuesto {cod_presupuesto}: {str(e)}")
            return None
        finally:
            cur.close(); con.close()
