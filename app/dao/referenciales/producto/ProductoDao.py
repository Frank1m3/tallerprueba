from flask import current_app as app
from app.conexion.Conexion import Conexion
from app.dao.referenciales.producto.producto_dto import ProductoDto

class ProductoDao:

    # ================================
    # Obtener todos los productos (items) con stock real
    # ================================
    def get_productos(self, id_sucursal=None, id_deposito=None):
        # Traemos stock de la tabla stock, si no hay devuelve 0
        sql = """
        SELECT 
            i.id_item,
            i.descripcion,
            COALESCE(s.cantidad, 0) AS cantidad,
            COALESCE(i.precio_unitario, 0) AS precio_unitario,
            i.item_code,
            i.id_proveedor,
            COALESCE(p.prov_nombre, '') AS prov_nombre
        FROM public.item i
        LEFT JOIN public.proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN public.stock s 
            ON s.id_item = i.id_item
            AND (%s IS NULL OR s.id_sucursal = %s)
            AND (%s IS NULL OR s.id_deposito = %s)
        WHERE i.activo = TRUE
        ORDER BY i.descripcion
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal, id_sucursal, id_deposito, id_deposito))
            filas = cur.fetchall()
            productos = []
            for f in filas:
                productos.append(ProductoDto(
                    id_producto=f[0],
                    nombre=f[1],
                    cantidad=float(f[2]),
                    precio_unitario=float(f[3]),
                    item_code=f[4] or '',
                    id_proveedor=f[5],
                    proveedor_nombre=f[6] or ''
                ))
            return productos
        except Exception as e:
            app.logger.error(f"Error al obtener productos: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener producto por ID
    # ================================
    def get_producto_by_id(self, id_producto, id_sucursal=None, id_deposito=None):
        sql = """
        SELECT 
            i.id_item,
            i.descripcion,
            COALESCE(s.cantidad, 0) AS cantidad,
            COALESCE(i.precio_unitario, 0) AS precio_unitario,
            i.item_code,
            i.id_proveedor,
            COALESCE(p.prov_nombre, '') AS prov_nombre
        FROM public.item i
        LEFT JOIN public.proveedor p ON p.id_proveedor = i.id_proveedor
        LEFT JOIN public.stock s 
            ON s.id_item = i.id_item
            AND (%s IS NULL OR s.id_sucursal = %s)
            AND (%s IS NULL OR s.id_deposito = %s)
        WHERE i.id_item = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_sucursal, id_sucursal, id_deposito, id_deposito, id_producto))
            f = cur.fetchone()
            if f:
                return ProductoDto(
                    id_producto=f[0],
                    nombre=f[1],
                    cantidad=float(f[2]),
                    precio_unitario=float(f[3]),
                    item_code=f[4] or '',
                    id_proveedor=f[5],
                    proveedor_nombre=f[6] or ''
                )
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener producto por ID: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()
