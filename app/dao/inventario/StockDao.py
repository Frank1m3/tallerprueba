from flask import current_app as app
from app.conexion.Conexion import Conexion


class StockDao:
    """Operaciones centralizadas de inventario por sucursal/depósito."""

    def incrementar(self, cur, id_sucursal: int, id_deposito: int, id_item: int, cantidad: float) -> None:
        if cantidad <= 0:
            return
        cur.execute("""
            INSERT INTO stock (id_sucursal, id_deposito, id_item, cantidad, fecha_ultima_actualizacion)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (id_sucursal, id_deposito, id_item)
            DO UPDATE SET
                cantidad = stock.cantidad + EXCLUDED.cantidad,
                fecha_ultima_actualizacion = NOW()
        """, (id_sucursal, id_deposito, id_item, cantidad))

    def decrementar(self, cur, id_sucursal: int, id_deposito: int, id_item: int, cantidad: float) -> bool:
        if cantidad <= 0:
            return True
        cur.execute("""
            UPDATE stock
            SET cantidad = cantidad - %s,
                fecha_ultima_actualizacion = NOW()
            WHERE id_item = %s
              AND id_sucursal = %s
              AND id_deposito = %s
              AND cantidad >= %s
        """, (cantidad, id_item, id_sucursal, id_deposito, cantidad))
        return cur.rowcount > 0

    def obtener_cantidad(self, id_sucursal: int, id_deposito: int, id_item: int) -> float:
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(cantidad, 0)
                FROM stock
                WHERE id_sucursal = %s AND id_deposito = %s AND id_item = %s
            """, (id_sucursal, id_deposito, id_item))
            row = cur.fetchone()
            return float(row[0]) if row else 0.0
        except Exception as e:
            app.logger.error(f"Error al obtener stock: {e}")
            return 0.0
        finally:
            cur.close()
            con.close()
