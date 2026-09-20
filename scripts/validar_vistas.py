"""Pruebas de validación de las vistas (app/codigos_sql/vistas.sql).

Comprueba, contra las tablas base:
  - exactitud: cada vista devuelve lo mismo que la consulta equivalente sobre las tablas
  - seguridad: v_seg_usuarios no expone la contraseña; rol_reportes no ve la tabla usuarios
  - rendimiento: las vistas grandes responden bajo un umbral usando índices
  - documentación: todas las vistas tienen COMMENT
Ejecutar:  python scripts/validar_vistas.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.conexion.Conexion import Conexion

con = Conexion().getConexion()
cur = con.cursor()
fallas = []


def uno(sql, params=None):
    cur.execute(sql, params or ())
    return cur.fetchone()[0]


def chequear(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: vista={obtenido} base={esperado}")
    if not ok:
        fallas.append(nombre)


print("== Exactitud ==")
chequear("v_inv_stock_detalle filas = stock",
         uno("SELECT COUNT(*) FROM v_inv_stock_detalle"), uno("SELECT COUNT(*) FROM stock"))
chequear("v_inv_stock_detalle SUM(stock) = stock",
         uno("SELECT COALESCE(SUM(stock_actual),0) FROM v_inv_stock_detalle"), uno("SELECT COALESCE(SUM(cantidad),0) FROM stock"))
chequear("v_inv_stock_detalle SIN_STOCK = stock<=0",
         uno("SELECT COUNT(*) FROM v_inv_stock_detalle WHERE nivel_stock='SIN_STOCK'"), uno("SELECT COUNT(*) FROM stock WHERE cantidad<=0"))
chequear("v_ven_ventas_diarias total = ventas PAGADO",
         uno("SELECT COALESCE(SUM(total_vendido),0) FROM v_ven_ventas_diarias"),
         uno("SELECT COALESCE(SUM(total_venta),0) FROM venta_cab WHERE estado='PAGADO'"))
chequear("v_ven_ventas_diarias unidades = detalle PAGADO",
         uno("SELECT COALESCE(SUM(unidades_vendidas),0) FROM v_ven_ventas_diarias"),
         uno("SELECT COALESCE(SUM(vd.cantidad),0) FROM venta_det vd JOIN venta_cab v USING (id_venta_cab) WHERE v.estado='PAGADO'"))
chequear("v_ven_venta_detalle filas = venta_det",
         uno("SELECT COUNT(*) FROM v_ven_venta_detalle"), uno("SELECT COUNT(*) FROM venta_det"))
chequear("v_inv_item_ventas unidades = detalle PAGADO con item",
         uno("SELECT COALESCE(SUM(unidades_vendidas),0) FROM v_inv_item_ventas"),
         uno("SELECT COALESCE(SUM(vd.cantidad),0) FROM venta_det vd JOIN venta_cab v USING (id_venta_cab) JOIN item i ON i.item_code=vd.item_code WHERE v.estado='PAGADO'"))
for vista, tabla in [('v_com_solicitud', 'solicitud_compra_cab'), ('v_com_presupuesto', 'presupuesto_compra_cab'),
                     ('v_com_pedido', 'pedido_compra_cab'), ('v_com_factura', 'factura_compra_cab'),
                     ('v_com_libro_compras', 'libro_compras'), ('v_seg_usuarios', 'usuarios')]:
    chequear(f"{vista} filas = {tabla}", uno(f"SELECT COUNT(*) FROM {vista}"), uno(f"SELECT COUNT(*) FROM {tabla}"))
chequear("v_com_pedido total = suma del detalle",
         float(uno("SELECT COALESCE(SUM(total_pedido),0) FROM v_com_pedido")),
         float(uno("SELECT COALESCE(SUM(cant_pedido*costo_unitario),0) FROM pedido_compra_det")))
chequear("v_seg_permisos filas = permisos",
         uno("SELECT COUNT(*) FROM v_seg_permisos"), uno("SELECT COUNT(*) FROM permisos"))

print("== Seguridad ==")
cols = uno("SELECT string_agg(column_name, ',') FROM information_schema.columns WHERE table_name='v_seg_usuarios'")
chequear("v_seg_usuarios no expone usu_clave", 'usu_clave' in cols, False)
cur.execute("SELECT has_table_privilege('rol_reportes','usuarios','SELECT'), has_table_privilege('rol_reportes','v_seg_usuarios','SELECT')")
sobre_tabla, sobre_vista = cur.fetchone()
chequear("rol_reportes NO lee la tabla usuarios", sobre_tabla, False)
chequear("rol_reportes SÍ lee v_seg_usuarios", sobre_vista, True)

print("== Rendimiento (stock ~344.000 filas, item ~86.000) ==")
for nombre, sql in [
    ("SIN_STOCK en v_inv_stock_detalle", "SELECT * FROM v_inv_stock_detalle WHERE nivel_stock = 'SIN_STOCK'"),
    ("un producto en v_inv_stock_detalle", "SELECT * FROM v_inv_stock_detalle WHERE id_item = 1"),
    ("v_inv_item_ventas", "SELECT * FROM v_inv_item_ventas"),
    ("v_ven_ventas_diarias", "SELECT * FROM v_ven_ventas_diarias"),
]:
    t0 = time.perf_counter(); cur.execute(sql); filas = len(cur.fetchall()); ms = (time.perf_counter() - t0) * 1000
    ok = ms < 3000
    print(f"  [{'OK' if ok else 'LENTO'}] {nombre}: {filas} filas en {ms:.0f} ms")
    if not ok:
        fallas.append(nombre)

print("== Documentación ==")
cur.execute("SELECT viewname FROM pg_views WHERE schemaname='public' AND viewname LIKE 'v\\_%'")
for (v,) in cur.fetchall():
    ok = uno("SELECT obj_description(%s::regclass)", (v,)) is not None
    print(f"  [{'OK' if ok else 'FALTA'}] COMMENT en {v}")
    if not ok:
        fallas.append('comment ' + v)

print("\nRESULTADO:", "TODO OK" if not fallas else f"FALLAS: {fallas}")
cur.close(); con.close()
sys.exit(1 if fallas else 0)
