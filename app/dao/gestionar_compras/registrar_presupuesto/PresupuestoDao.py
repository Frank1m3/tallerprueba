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
