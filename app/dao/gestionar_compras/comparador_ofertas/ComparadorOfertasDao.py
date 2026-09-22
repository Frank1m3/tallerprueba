from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2


class ComparadorOfertasDao:
    """Compara las cotizaciones (presupuestos) que los proveedores enviaron para una solicitud
    aprobada y permite seleccionar la ganadora."""

    def solicitudes_con_cotizaciones(self):
        """Solicitudes APROBADAS, con la cantidad de cotizaciones vigentes de cada una."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT sc.id_solicitud, sc.nro_solicitud, sc.fecha_solicitud, sc.fecha_necesaria,
                       sc.solicitante, sc.sucursal,
                       (SELECT COUNT(*) FROM presupuesto_compra_cab pc
                         WHERE pc.id_solicitud = sc.id_solicitud AND pc.estado <> 'ANULADO') AS cotizaciones
                FROM v_com_solicitud sc
                WHERE sc.estado::text = 'APROBADA'
                ORDER BY sc.id_solicitud DESC
            """)
            return [{
                "id_solicitud": r[0], "nro_solicitud": r[1],
                "fecha_solicitud": r[2].strftime("%Y-%m-%d") if r[2] else None,
                "fecha_necesaria": r[3].strftime("%Y-%m-%d") if r[3] else None,
                "solicitante": r[4] or '', "sucursal": r[5] or '', "cotizaciones": r[6]
            } for r in cur.fetchall()]
        except psycopg2.Error as e:
            app.logger.error(f"Error en solicitudes_con_cotizaciones: {e}")
            return []
        finally:
            cur.close(); con.close()

    def comparar(self, nro_solicitud):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""SELECT id_solicitud, nro_solicitud, estado::text, fecha_solicitud, fecha_necesaria,
                                  solicitante, sucursal
                           FROM v_com_solicitud WHERE nro_solicitud = %s""", (nro_solicitud,))
            sol = cur.fetchone()
            if not sol or sol[2] != 'APROBADA':
                return None
            id_solicitud = sol[0]

            cur.execute("""
                SELECT i.item_code, i.descripcion, sd.cantidad
                FROM solicitud_compra_det sd JOIN item i ON i.id_item = sd.id_item
                WHERE sd.id_solicitud = %s ORDER BY i.descripcion
            """, (id_solicitud,))
            items = [{"item_code": r[0], "descripcion": r[1], "cantidad": float(r[2])} for r in cur.fetchall()]

            cur.execute("""
                SELECT pc.id_pre_compra_cab, pc.cod_presupuesto, pc.estado, pc.fecha_emision, pc.fecha_vencimiento,
                       pc.id_proveedor, COALESCE(p.prov_nombre, '(sin proveedor)')
                FROM presupuesto_compra_cab pc
                LEFT JOIN proveedor p ON p.id_proveedor = pc.id_proveedor
                WHERE pc.id_solicitud = %s AND pc.estado <> 'ANULADO'
                ORDER BY pc.id_pre_compra_cab
            """, (id_solicitud,))
            cabeceras = cur.fetchall()

            precios = {}
            if cabeceras:
                cur.execute("""SELECT id_pre_compra_cab, item_code, precio_unitario
                               FROM presupuesto_compra_det WHERE id_pre_compra_cab = ANY(%s)""",
                            ([c[0] for c in cabeceras],))
                for id_pre, code, precio in cur.fetchall():
                    precios.setdefault(id_pre, {})[str(code)] = float(precio)

            ofertas = []
            for c in cabeceras:
                p = precios.get(c[0], {})
                cotizados = {it["item_code"]: p[it["item_code"]] for it in items if p.get(it["item_code"], 0) > 0}
                total = sum(cotizados[it["item_code"]] * it["cantidad"] for it in items if it["item_code"] in cotizados)
                ofertas.append({
                    "id_presupuesto": c[0], "cod_presupuesto": c[1], "estado": c[2],
                    "fecha_emision": c[3].strftime("%Y-%m-%d") if c[3] else None,
                    "fecha_vencimiento": c[4].strftime("%Y-%m-%d") if c[4] else None,
                    "id_proveedor": c[5], "proveedor": c[6],
                    "precios": cotizados, "total": round(total, 2),
                    "completa": len(cotizados) == len(items) and len(items) > 0,
                    "faltantes": len(items) - len(cotizados)
                })

            completas = [o for o in ofertas if o["completa"]]
            mejor = min(completas, key=lambda o: o["total"])["id_presupuesto"] if completas else None
            mejores_precios = {}
            for it in items:
                vals = [o["precios"][it["item_code"]] for o in ofertas if it["item_code"] in o["precios"]]
                if vals:
                    mejores_precios[it["item_code"]] = min(vals)

            return {
                "solicitud": {"id_solicitud": sol[0], "nro_solicitud": sol[1],
                              "fecha_solicitud": sol[3].strftime("%Y-%m-%d") if sol[3] else None,
                              "fecha_necesaria": sol[4].strftime("%Y-%m-%d") if sol[4] else None,
                              "solicitante": sol[5] or '', "sucursal": sol[6] or ''},
                "items": items, "ofertas": ofertas,
                "mejor_oferta": mejor, "mejores_precios": mejores_precios
            }
        except psycopg2.Error as e:
            app.logger.error(f"Error en comparar: {e}")
            return None
        finally:
            cur.close(); con.close()

    def seleccionar(self, id_presupuesto):
        """Aprueba la oferta elegida y rechaza las demás de la misma solicitud.
        Devuelve (ok, mensaje_de_error)."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT pc.id_solicitud, pc.estado, sc.estado::text
                FROM presupuesto_compra_cab pc
                LEFT JOIN solicitud_compra_cab sc ON sc.id_solicitud = pc.id_solicitud
                WHERE pc.id_pre_compra_cab = %s
            """, (id_presupuesto,))
            fila = cur.fetchone()
            if not fila or not fila[0]:
                return False, 'La oferta no existe.'
            id_solicitud, estado_pre, estado_sol = fila
            if estado_pre == 'ANULADO':
                return False, 'La oferta está anulada.'
            if estado_sol != 'APROBADA':
                return False, 'La solicitud no está aprobada.'

            # Si otra oferta ya originó un pedido vigente, no se puede cambiar la selección
            cur.execute("""
                SELECT 1 FROM pedido_compra_cab pd
                JOIN presupuesto_compra_cab pc ON pc.id_pre_compra_cab = pd.id_pre_compra_cab
                WHERE pc.id_solicitud = %s AND pc.id_pre_compra_cab <> %s AND pd.estado <> 'ANULADO' LIMIT 1
            """, (id_solicitud, id_presupuesto))
            if cur.fetchone():
                return False, 'Ya se generó un pedido con otra oferta de esta solicitud. Anulá ese pedido antes de cambiar la selección.'

            cur.execute("""UPDATE presupuesto_compra_cab SET estado = 'RECHAZADO'
                           WHERE id_solicitud = %s AND id_pre_compra_cab <> %s AND estado IN ('PENDIENTE', 'APROBADO')""",
                        (id_solicitud, id_presupuesto))
            cur.execute("UPDATE presupuesto_compra_cab SET estado = 'APROBADO' WHERE id_pre_compra_cab = %s", (id_presupuesto,))
            con.commit()
            return True, None
        except psycopg2.Error as e:
            con.rollback()
            app.logger.error(f"Error al seleccionar oferta: {e}")
            return False, 'No se pudo registrar la selección.'
        finally:
            cur.close(); con.close()
