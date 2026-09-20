from flask import current_app as app
from app.conexion.Conexion import Conexion
from datetime import date, timedelta
import psycopg2


def _dias_periodo(desde, hasta):
    d = date.fromisoformat(desde)
    h = date.fromisoformat(hasta)
    return max((h - d).days + 1, 1)


def _periodo_anterior(desde, hasta):
    dias = _dias_periodo(desde, hasta)
    d = date.fromisoformat(desde)
    anterior_hasta = d - timedelta(days=1)
    anterior_desde = anterior_hasta - timedelta(days=dias - 1)
    return anterior_desde.isoformat(), anterior_hasta.isoformat()


def _variacion(actual, anterior):
    if not anterior:
        return None
    return round((float(actual) - float(anterior)) / float(anterior) * 100, 1)


class DashboardDao:

    # ---- Stock agregado por item (suma entre depósitos si no se filtra uno) ----
    def _sql_stock_agg(self):
        return """
            SELECT s.id_item, SUM(s.cantidad) AS stock_actual
            FROM stock s
            WHERE (%(id_sucursal)s IS NULL OR s.id_sucursal = %(id_sucursal)s)
              AND (%(id_deposito)s IS NULL OR s.id_deposito = %(id_deposito)s)
            GROUP BY s.id_item
        """

    def _total_unidades_periodo(self, cur, desde, hasta, id_sucursal):
        cur.execute("""
            SELECT COALESCE(SUM(vd.cantidad), 0)
            FROM venta_det vd
            JOIN venta_cab v ON v.id_venta_cab = vd.id_venta_cab
            WHERE v.estado = 'PAGADO'
              AND v.fecha_venta BETWEEN %(desde)s AND %(hasta)s
              AND (%(id_sucursal)s IS NULL OR v.id_sucursal = %(id_sucursal)s)
        """, {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal})
        return float(cur.fetchone()[0])

    def top_vendidos(self, cur, desde, hasta, id_sucursal, limit=10):
        cur.execute(f"""
            SELECT i.id_item, i.item_code, i.descripcion,
                   SUM(vd.cantidad) AS unidades,
                   SUM(vd.cantidad * vd.precio_unitario) AS facturacion
            FROM venta_det vd
            JOIN venta_cab v ON v.id_venta_cab = vd.id_venta_cab
            JOIN item i ON i.item_code = vd.item_code
            WHERE v.estado = 'PAGADO'
              AND v.fecha_venta BETWEEN %(desde)s AND %(hasta)s
              AND (%(id_sucursal)s IS NULL OR v.id_sucursal = %(id_sucursal)s)
            GROUP BY i.id_item, i.item_code, i.descripcion
            ORDER BY unidades DESC
            LIMIT %(limit)s
        """, {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal, "limit": limit})
        filas = cur.fetchall()
        total = self._total_unidades_periodo(cur, desde, hasta, id_sucursal)
        maximo = float(filas[0][3]) if filas else 0
        return [{
            "id_item": r[0], "item_code": r[1], "descripcion": r[2],
            "unidades": float(r[3]), "facturacion": float(r[4]),
            "porcentaje_participacion": round(float(r[3]) / total * 100, 1) if total else 0,
            "porcentaje_barra": round(float(r[3]) / maximo * 100, 1) if maximo else 0
        } for r in filas]

    def menos_vendidos(self, cur, desde, hasta, id_sucursal, id_deposito, limit=10):
        cur.execute(f"""
            WITH ventas AS (
                SELECT i.id_item, i.item_code, i.descripcion,
                       SUM(vd.cantidad) AS unidades, MAX(v.fecha_venta) AS ultima_venta
                FROM venta_det vd
                JOIN venta_cab v ON v.id_venta_cab = vd.id_venta_cab
                JOIN item i ON i.item_code = vd.item_code
                WHERE v.estado = 'PAGADO'
                  AND v.fecha_venta BETWEEN %(desde)s AND %(hasta)s
                  AND (%(id_sucursal)s IS NULL OR v.id_sucursal = %(id_sucursal)s)
                GROUP BY i.id_item, i.item_code, i.descripcion
            ),
            stock_agg AS ({self._sql_stock_agg()})
            SELECT v.id_item, v.item_code, v.descripcion, v.unidades, v.ultima_venta,
                   COALESCE(sa.stock_actual, 0) AS stock_actual
            FROM ventas v
            LEFT JOIN stock_agg sa ON sa.id_item = v.id_item
            ORDER BY v.unidades ASC, v.descripcion
            LIMIT %(limit)s
        """, {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal,
              "id_deposito": id_deposito, "limit": limit})
        hoy = date.today()
        return [{
            "id_item": r[0], "item_code": r[1], "descripcion": r[2],
            "unidades": float(r[3]),
            "ultima_venta": r[4].isoformat() if r[4] else None,
            "dias_ultima_venta": (hoy - r[4]).days if r[4] else None,
            "stock_actual": float(r[5])
        } for r in cur.fetchall()]

    def mayor_rotacion(self, cur, desde, hasta, id_sucursal, id_deposito, limit=10):
        dias = _dias_periodo(desde, hasta)
        cur.execute(f"""
            WITH ventas AS (
                SELECT i.id_item, i.item_code, i.descripcion, i.cantidad_minima,
                       SUM(vd.cantidad) AS unidades
                FROM venta_det vd
                JOIN venta_cab v ON v.id_venta_cab = vd.id_venta_cab
                JOIN item i ON i.item_code = vd.item_code
                WHERE v.estado = 'PAGADO'
                  AND v.fecha_venta BETWEEN %(desde)s AND %(hasta)s
                  AND (%(id_sucursal)s IS NULL OR v.id_sucursal = %(id_sucursal)s)
                GROUP BY i.id_item, i.item_code, i.descripcion, i.cantidad_minima
            ),
            stock_agg AS ({self._sql_stock_agg()})
            SELECT v.id_item, v.item_code, v.descripcion, v.unidades,
                   COALESCE(sa.stock_actual, 0) AS stock_actual, v.cantidad_minima
            FROM ventas v
            LEFT JOIN stock_agg sa ON sa.id_item = v.id_item
            ORDER BY v.unidades DESC
            LIMIT %(limit)s
        """, {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal,
              "id_deposito": id_deposito, "limit": limit})
        out = []
        for r in cur.fetchall():
            unidades, stock_actual = float(r[3]), float(r[4])
            minima = float(r[5]) if r[5] is not None else None
            velocidad = round(unidades / dias, 2)
            cobertura = round(stock_actual / velocidad, 1) if velocidad > 0 else None
            out.append({
                "id_item": r[0], "item_code": r[1], "descripcion": r[2],
                "velocidad_diaria": velocidad, "stock_actual": stock_actual,
                "cobertura_dias": cobertura,
                "nivel": self._nivel_riesgo(stock_actual, minima, cobertura)
            })
        return out

    @staticmethod
    def _nivel_riesgo(stock_actual, cantidad_minima, cobertura_dias=None):
        if stock_actual <= 0:
            return "sin_stock"
        if cobertura_dias is not None and cobertura_dias <= 2:
            return "critico"
        if not cantidad_minima or cantidad_minima <= 0:
            return "normal"
        ratio = stock_actual / cantidad_minima
        if ratio <= 0.5:
            return "critico"
        if ratio <= 1.0:
            return "bajo"
        if ratio <= 1.5:
            return "atencion"
        return "normal"

    def riesgo_stock(self, cur, desde, hasta, id_sucursal, id_deposito, limit=10, offset=0, q=None):
        condicion_q = "AND (i.descripcion ILIKE %(q)s OR i.item_code ILIKE %(q)s)" if q else ""
        cur.execute(f"""
            WITH stock_agg AS ({self._sql_stock_agg()}),
            ventas_periodo AS (
                SELECT i.id_item, SUM(vd.cantidad) AS unidades
                FROM venta_det vd
                JOIN venta_cab v ON v.id_venta_cab = vd.id_venta_cab
                JOIN item i ON i.item_code = vd.item_code
                WHERE v.estado = 'PAGADO' AND v.fecha_venta BETWEEN %(desde)s AND %(hasta)s
                  AND (%(id_sucursal)s IS NULL OR v.id_sucursal = %(id_sucursal)s)
                GROUP BY i.id_item
            )
            SELECT i.id_item, i.item_code, i.descripcion, sa.stock_actual, i.cantidad_minima,
                   COALESCE(vp.unidades, 0) AS unidades_periodo,
                   COUNT(*) OVER() AS total_filas
            FROM item i
            JOIN stock_agg sa ON sa.id_item = i.id_item
            LEFT JOIN ventas_periodo vp ON vp.id_item = i.id_item
            WHERE i.activo = TRUE
              AND i.cantidad_minima IS NOT NULL AND i.cantidad_minima > 0
              AND sa.stock_actual > 0
              AND sa.stock_actual <= i.cantidad_minima * 1.5
              {condicion_q}
            ORDER BY (sa.stock_actual / i.cantidad_minima) ASC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"desde": desde, "hasta": hasta, "id_sucursal": id_sucursal,
              "id_deposito": id_deposito, "limit": limit, "offset": offset,
              "q": f"%{q}%" if q else None})
        dias = _dias_periodo(desde, hasta)
        filas = cur.fetchall()
        total = filas[0][6] if filas else 0
        out = []
        for r in filas:
            stock_actual, minima, unidades = float(r[3]), float(r[4]), float(r[5])
            velocidad = round(unidades / dias, 2) if unidades else 0
            cobertura = round(stock_actual / velocidad, 1) if velocidad > 0 else None
            out.append({
                "id_item": r[0], "item_code": r[1], "descripcion": r[2],
                "stock_actual": stock_actual, "cantidad_minima": minima,
                "cobertura_dias": cobertura,
                "nivel": self._nivel_riesgo(stock_actual, minima, cobertura)
            })
        return out, total

    def sin_stock(self, cur, id_sucursal, id_deposito, limit=10, offset=0, q=None):
        condicion_q = "AND (i.descripcion ILIKE %(q)s OR i.item_code ILIKE %(q)s)" if q else ""
        cur.execute(f"""
            WITH stock_agg AS ({self._sql_stock_agg()}),
            ultima_venta AS (
                SELECT id_item, ultima_venta AS fecha FROM v_inv_item_ventas
            ),
            ultima_recepcion AS (
                SELECT i.id_item, MAX(rc.fecha_recepcion) AS fecha
                FROM recepcion_det rd
                JOIN recepcion_cab rc ON rc.id_recepcion = rd.id_recepcion
                JOIN item i ON i.item_code = rd.item_code
                GROUP BY i.id_item
            )
            SELECT i.id_item, i.item_code, i.descripcion, sa.stock_actual, i.cantidad_minima,
                   uv.fecha AS ultima_venta, ur.fecha AS ultima_recepcion,
                   p.prov_nombre, i.id_proveedor,
                   COUNT(*) OVER() AS total_filas
            FROM item i
            JOIN stock_agg sa ON sa.id_item = i.id_item
            LEFT JOIN ultima_venta uv ON uv.id_item = i.id_item
            LEFT JOIN ultima_recepcion ur ON ur.id_item = i.id_item
            LEFT JOIN proveedor p ON p.id_proveedor = i.id_proveedor
            WHERE i.activo = TRUE AND sa.stock_actual <= 0
              {condicion_q}
            ORDER BY i.descripcion
            LIMIT %(limit)s OFFSET %(offset)s
        """, {"id_sucursal": id_sucursal, "id_deposito": id_deposito,
              "limit": limit, "offset": offset, "q": f"%{q}%" if q else None})
        filas = cur.fetchall()
        total = filas[0][9] if filas else 0
        out = []
        for r in filas:
            stock_actual, minima = float(r[3]), float(r[4]) if r[4] is not None else 0.0
            sugerido = max(minima - stock_actual, minima, 0)
            out.append({
                "id_item": r[0], "item_code": r[1], "descripcion": r[2],
                "stock_actual": stock_actual, "cantidad_minima": minima,
                "ultima_venta": r[5].isoformat() if r[5] else None,
                "ultima_recepcion": r[6].isoformat() if r[6] else None,
                "proveedor": r[7], "id_proveedor": r[8],
                "cantidad_sugerida": sugerido
            })
        return out, total

    def sin_movimiento(self, cur, id_sucursal, id_deposito, dias_umbral=30, limit=10):
        limite = (date.today() - timedelta(days=dias_umbral)).isoformat()
        cur.execute(f"""
            WITH stock_agg AS ({self._sql_stock_agg()}),
            ultima_venta AS (
                SELECT id_item, ultima_venta AS fecha FROM v_inv_item_ventas
            )
            SELECT i.id_item, i.item_code, i.descripcion, sa.stock_actual, uv.fecha
            FROM item i
            JOIN stock_agg sa ON sa.id_item = i.id_item
            LEFT JOIN ultima_venta uv ON uv.id_item = i.id_item
            WHERE i.activo = TRUE
              AND (uv.fecha IS NULL OR uv.fecha < %(limite)s)
            ORDER BY uv.fecha ASC NULLS FIRST
            LIMIT %(limit)s
        """, {"id_sucursal": id_sucursal, "id_deposito": id_deposito,
              "limite": limite, "limit": limit})
        hoy = date.today()
        return [{
            "id_item": r[0], "item_code": r[1], "descripcion": r[2],
            "stock_actual": float(r[3]),
            "ultima_venta": r[4].isoformat() if r[4] else None,
            "dias_sin_venta": (hoy - r[4]).days if r[4] else None
        } for r in cur.fetchall()]

    def _conteos_stock(self, cur, id_sucursal, id_deposito):
        cur.execute(f"""
            WITH stock_agg AS ({self._sql_stock_agg()})
            SELECT
                COUNT(*) FILTER (WHERE sa.stock_actual <= 0) AS sin_stock,
                COUNT(*) FILTER (
                    WHERE sa.stock_actual > 0 AND i.cantidad_minima > 0
                      AND sa.stock_actual <= i.cantidad_minima
                ) AS bajo_minimo,
                COUNT(*) FILTER (
                    WHERE sa.stock_actual > 0 AND i.cantidad_minima > 0
                      AND sa.stock_actual <= i.cantidad_minima * 1.5
                ) AS proximos_quebrar
            FROM item i
            JOIN stock_agg sa ON sa.id_item = i.id_item
            WHERE i.activo = TRUE
        """, {"id_sucursal": id_sucursal, "id_deposito": id_deposito})
        r = cur.fetchone()
        return {"sin_stock": r[0], "bajo_minimo": r[1], "proximos_quebrar": r[2]}

    def _conteo_sin_movimiento(self, cur, id_sucursal, id_deposito, dias_umbral):
        limite = (date.today() - timedelta(days=dias_umbral)).isoformat()
        cur.execute(f"""
            WITH stock_agg AS ({self._sql_stock_agg()}),
            ultima_venta AS (
                SELECT id_item, ultima_venta AS fecha FROM v_inv_item_ventas
            )
            SELECT COUNT(*)
            FROM item i
            JOIN stock_agg sa ON sa.id_item = i.id_item
            LEFT JOIN ultima_venta uv ON uv.id_item = i.id_item
            WHERE i.activo = TRUE AND (uv.fecha IS NULL OR uv.fecha < %(limite)s)
        """, {"id_sucursal": id_sucursal, "id_deposito": id_deposito, "limite": limite})
        return cur.fetchone()[0]

    # ---- Endpoint agregado: todo lo que necesita el dashboard en un solo viaje ----
    def obtener_resumen(self, desde, hasta, id_sucursal=None, id_deposito=None, dias_sin_movimiento=30):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            top = self.top_vendidos(cur, desde, hasta, id_sucursal)
            menos = self.menos_vendidos(cur, desde, hasta, id_sucursal, id_deposito)
            rotacion = self.mayor_rotacion(cur, desde, hasta, id_sucursal, id_deposito)
            riesgo, total_riesgo = self.riesgo_stock(cur, desde, hasta, id_sucursal, id_deposito, limit=10)
            sinstock, total_sinstock = self.sin_stock(cur, id_sucursal, id_deposito, limit=10)
            sinmov = self.sin_movimiento(cur, id_sucursal, id_deposito, dias_sin_movimiento)
            conteos = self._conteos_stock(cur, id_sucursal, id_deposito)
            conteo_sinmov = self._conteo_sin_movimiento(cur, id_sucursal, id_deposito, dias_sin_movimiento)

            anterior_desde, anterior_hasta = _periodo_anterior(desde, hasta)
            total_actual = self._total_unidades_periodo(cur, desde, hasta, id_sucursal)
            total_anterior = self._total_unidades_periodo(cur, anterior_desde, anterior_hasta, id_sucursal)

            kpi_mas_vendido = top[0] if top else None
            kpi_menos_vendido = menos[0] if menos else None

            kpis = {
                "unidades_periodo": total_actual,
                "variacion_unidades": _variacion(total_actual, total_anterior),
                "mas_vendido": kpi_mas_vendido,
                "menos_vendido": kpi_menos_vendido,
                "sin_stock": conteos["sin_stock"],
                "bajo_minimo": conteos["bajo_minimo"],
                "proximos_quebrar": conteos["proximos_quebrar"],
                "sin_movimiento": conteo_sinmov,
                "mayor_rotacion": rotacion[0] if rotacion else None
            }

            analisis_rapido = {
                "mas_vendido": kpi_mas_vendido,
                "menos_vendido": kpi_menos_vendido,
                "mayor_rotacion": rotacion[0] if rotacion else None,
                "mayor_riesgo": riesgo[0] if riesgo else None,
                "sin_movimiento_top": sinmov[0] if sinmov else None
            }

            return {
                "kpis": kpis,
                "top_vendidos": top,
                "menos_vendidos": menos,
                "mayor_rotacion": rotacion,
                "riesgo_stock": riesgo, "riesgo_stock_total": total_riesgo,
                "sin_stock": sinstock, "sin_stock_total": total_sinstock,
                "sin_movimiento": sinmov,
                "analisis_rapido": analisis_rapido
            }
        except psycopg2.Error as e:
            app.logger.error(f"Error en obtener_resumen dashboard: {e}")
            return None
        finally:
            cur.close(); con.close()

    def riesgo_stock_paginado(self, desde, hasta, id_sucursal, id_deposito, limit, offset, q=None):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            return self.riesgo_stock(cur, desde, hasta, id_sucursal, id_deposito, limit, offset, q)
        except psycopg2.Error as e:
            app.logger.error(f"Error en riesgo_stock_paginado: {e}")
            return [], 0
        finally:
            cur.close(); con.close()

    def sin_stock_paginado(self, id_sucursal, id_deposito, limit, offset, q=None):
        con = Conexion().getConexion()
        cur = con.cursor()
        try:
            return self.sin_stock(cur, id_sucursal, id_deposito, limit, offset, q)
        except psycopg2.Error as e:
            app.logger.error(f"Error en sin_stock_paginado: {e}")
            return [], 0
        finally:
            cur.close(); con.close()
