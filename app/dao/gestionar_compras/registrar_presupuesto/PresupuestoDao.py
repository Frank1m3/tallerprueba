from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_dto import PresupuestoCompraDto
from app.dao.gestionar_compras.registrar_presupuesto.dto.presupuesto_compra_detalle_dto import PresupuestoCompraDetalleDto
from app.dao.gestionar_compras.registrar_solicitud_compras.SolicitudCompraDao import SolicitudCompraDao

class PresupuestoCompraDao:
    """
    DAO para manejar operaciones de presupuesto de compra.
    """

    # ================================
    # Obtener siguiente código
    # ================================
    def obtener_siguiente_codigo(self) -> int:
        sql = "SELECT COALESCE(MAX(id_pre_compra_cab), 0) + 1 FROM presupuesto_compra_cab"
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            return cur.fetchone()[0]
        finally:
            cur.close()
            con.close()

    # ================================
    # Insertar cabecera + detalles
    # ================================
    def insertar(self, dto: PresupuestoCompraDto) -> bool:
        sql_cab = """
            INSERT INTO presupuesto_compra_cab
            (cod_presupuesto, fun_id, id_proveedor, fecha_emision,
             fecha_vencimiento, condicion_compra, estado, archivo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id_pre_compra_cab
        """
        sql_det = """
            INSERT INTO presupuesto_compra_det
            (id_pre_compra_cab, item_code, cantidad, precio_unitario)
            VALUES (%s,%s,%s,%s)
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            con.autocommit = False
            cur.execute(sql_cab, (
                dto.cod_presupuesto,
                dto.fun_id,
                dto.id_proveedor,
                dto.fecha_emision if dto.fecha_emision else None,
                dto.fecha_vencimiento if dto.fecha_vencimiento else None,
                dto.condicion_compra if dto.condicion_compra else None,
                dto.estado,
                dto.archivo
            ))
            id_cab = cur.fetchone()[0]

            for d in dto.detalles:
                cur.execute(sql_det, (
                    id_cab,
                    d.item_code,
                    d.cantidad,
                    d.precio_unitario
                ))

            con.commit()
            return True
        except Exception as e:
            app.logger.error(f"Error insertar presupuesto: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()

    # ================================
    # Listar presupuestos (cabecera)
    # ================================
    def listar(self):
        sql = """
        SELECT c.id_pre_compra_cab,
               c.cod_presupuesto,
               c.fecha_emision,
               p.prov_nombre,
               c.estado,
               c.archivo
        FROM presupuesto_compra_cab c
        LEFT JOIN proveedor p ON p.id_proveedor = c.id_proveedor
        ORDER BY c.id_pre_compra_cab DESC
        """
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            return [
                dict(
                    id_pre_compra_cab=r[0],
                    cod_presupuesto=r[1],
                    fecha_emision=r[2].strftime("%Y-%m-%d") if r[2] else None,
                    proveedor=r[3],
                    estado=r[4],
                    archivo=r[5]
                )
                for r in cur.fetchall()
            ]
        finally:
            cur.close()
            con.close()
            
    # ================================
    # Buscar mercaderías por código, descripción o código de barras
    # ================================
    def buscar_mercaderias(self, filtro='', id_sucursal=None):
        sql = """
        SELECT i.id_item,
               i.item_code,
               i.descripcion,
               COALESCE(SUM(st.cantidad),0) AS stock,
               COALESCE(i.precio_unitario,0) AS precio_unitario,
               i.id_proveedor,
               COALESCE(barras_agg.barras,'') AS barras
        FROM item i
        LEFT JOIN stock st ON st.id_item = i.id_item
        LEFT JOIN (
            SELECT id_item, string_agg(cod_barra, ',') AS barras
            FROM barras
            GROUP BY id_item
        ) barras_agg ON barras_agg.id_item = i.id_item
        WHERE i.activo = TRUE
          AND (%s = '' OR i.item_code ILIKE %s OR i.descripcion ILIKE %s OR barras_agg.barras ILIKE %s)
        """
        params = [filtro, f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"]

        if id_sucursal and str(id_sucursal).isdigit():
            sql += " AND (st.id_sucursal = %s OR st.id_sucursal IS NULL)"
            params.append(int(id_sucursal))

        sql += """
        GROUP BY i.id_item, i.item_code, i.descripcion, i.precio_unitario, i.id_proveedor, barras_agg.barras
        ORDER BY i.descripcion
        """

        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, params)
            resultados = []
            for r in cur.fetchall():
                resultados.append({
                    'id_item': r[0],
                    'item_code': r[1],          # <-- agregado
                    'codigo': r[1],             # <-- compatibilidad front
                    'descripcion': r[2],
                    'stock': float(r[3]),
                    'precio_unitario': float(r[4]), # <-- agregado
                    'precio': float(r[4]),           # <-- compatibilidad front
                    'id_proveedor': r[5],
                    'barras': r[6].split(',') if r[6] else []
                })
            return resultados
        except Exception as e:
            app.logger.error(f"Error buscar mercaderías: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener datos de una solicitud de compra para presupuesto
    # ================================
    def obtener_solicitud_para_presupuesto(self, nro_solicitud: int):
        dao = SolicitudCompraDao()
        solicitud = dao.obtener_solicitud_por_nro(nro_solicitud)
        if not solicitud:
            return {'success': False, 'detalles': []}

        detalles = []
        for d in solicitud['detalles']:
            detalles.append({
                'id_item': d.get('id_item'),
                'item_code': d.get('id_item'),        # <-- agregado
                'codigo': d.get('id_item'),           # <-- compatibilidad front
                'descripcion': d.get('nombre_producto'),
                'stock': d.get('stock', 0),
                'cantidad': d.get('cantidad', 0),
                'precio_unitario': d.get('precio', 0), # <-- agregado
                'precio': d.get('precio', 0)          # <-- compatibilidad front
            })

        return {'success': True, 'detalles': detalles}
    # ================================
    # Obtener presupuesto completo por ID (cabecera + detalle)
    # ================================
    def obtener_por_id(self, id_pre_compra_cab):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT c.id_pre_compra_cab, c.cod_presupuesto, c.fecha_emision,
                       c.fecha_vencimiento, c.condicion_compra, c.estado, c.archivo,
                       c.id_proveedor, p.prov_nombre,
                       c.fun_id, f.nombres || ' ' || f.apellidos
                FROM presupuesto_compra_cab c
                LEFT JOIN proveedor p ON p.id_proveedor = c.id_proveedor
                LEFT JOIN funcionarios f ON f.fun_id = c.fun_id
                WHERE c.id_pre_compra_cab = %s
            """, (id_pre_compra_cab,))
            cab = cur.fetchone()
            if not cab:
                return None

            pres = {
                'id': cab[0],
                'cod_presupuesto': cab[1],
                'fecha_emision': cab[2].strftime("%Y-%m-%d") if cab[2] else None,
                'fecha_vencimiento': cab[3].strftime("%Y-%m-%d") if cab[3] else None,
                'condicion_compra': cab[4] or '',
                'estado': cab[5],
                'archivo': cab[6],
                'id_proveedor': cab[7],
                'proveedor': cab[8] or '',
                'fun_id': cab[9],
                'funcionario': cab[10] or '',
                'detalles': [],
                'total': 0.0
            }

            cur.execute("""
                SELECT d.item_code, i.descripcion, d.cantidad, d.precio_unitario
                FROM presupuesto_compra_det d
                LEFT JOIN item i ON i.item_code = d.item_code
                WHERE d.id_pre_compra_cab = %s
                ORDER BY d.item_code
            """, (id_pre_compra_cab,))
            total = 0.0
            for r in cur.fetchall():
                cant = float(r[2]); pu = float(r[3]); sub = cant * pu
                total += sub
                pres['detalles'].append({
                    'item_code': r[0],
                    'descripcion': r[1] or '',
                    'cantidad': cant,
                    'precio_unitario': pu,
                    'subtotal': sub
                })
            pres['total'] = total
            return pres
        except Exception as e:
            app.logger.error(f"Error obtener presupuesto por id: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Cambiar estado (solo desde PENDIENTE)
    # ================================
    def cambiar_estado(self, id_pre_compra_cab, nuevo_estado):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            cur.execute("SELECT estado FROM presupuesto_compra_cab WHERE id_pre_compra_cab = %s", (id_pre_compra_cab,))
            fila = cur.fetchone()
            if not fila:
                return False, 'No existe el presupuesto'
            if fila[0] != 'PENDIENTE':
                return False, f'El presupuesto ya está {fila[0]}'
            cur.execute("UPDATE presupuesto_compra_cab SET estado = %s WHERE id_pre_compra_cab = %s",
                        (nuevo_estado, id_pre_compra_cab))
            con.commit()
            return True, None
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error cambiar estado presupuesto: {e}")
            return False, str(e)
        finally:
            cur.close()
            con.close()
