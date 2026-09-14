"""
Migración one-off: trae todos los artículos de la BD "CAJA" (tabla articulolocal,
~86.070 filas) hacia la tabla "item" de la BD "TALLER", e inventa datos de
stock/cantidad_minima que no existen en el origen.

Decisiones tomadas junto al usuario (2026-09-13):
  - item_code = cod_articulo tal cual (como texto). Si choca con un item_code
    que ya existía en TALLER (los códigos '1'..'9' de los 18 items de prueba),
    se le agrega el sufijo "-CAJA" solo a esos pocos casos.
  - id_tipo_item: se deja NULL para todo lo importado (no se asigna categoría).
  - id_proveedor: se deja NULL (CAJA no tiene una tabla de proveedores con la
    que se pueda cruzar de forma confiable).
  - unidad_med / precio_unitario: se toman del registro más reciente de
    preciosartlocal para ese artículo (se prioriza cod_lista=2, que es la
    lista general/vigente; si no hay para esa lista se usa el precio más
    reciente de cualquier lista). sigla_venta -> unidad_medida:
    UN->Unidad, KG->Kilogramo, CJ->Paquete, LT->Unidad (fallback).
  - id_tipo_impuesto: pct_iva -> 10%->IVA 10%, 5%->IVA 5%, 0%->Exento,
    15%->IVA 15% (no aparece en los datos actuales pero se deja el mapeo).
  - activo: hab_venta = 'S' -> True, 'N' -> False.
  - cantidad_minima: no existe en el origen, se inventa (valor chico y
    determinístico según el código de artículo, para que sea reproducible
    si el script se corre de nuevo en un entorno de prueba).
  - Sucursales: además de las 2 existentes (ÑEMBY, ASUNCION) se crean LUQUE
    y ASUNCION-ROYAL. En las 4 sucursales se aseguran los depósitos BAZAR,
    CARNICERIA, PANADERIA, CONFITERIA, PATIO DE COMIDAS, POLLERIA,
    FIAMBRERIA y SALA (sin duplicar los que ya existían).
  - Stock: cada item importado recibe una fila de stock en el depósito SALA
    de CADA una de las 4 sucursales (cantidad inventada, independiente por
    sucursal), porque SALA es donde va "casi todo" según el usuario.

Toda la carga de items + stock corre dentro de UNA sola transacción sobre
TALLER: si algo falla a mitad de camino no queda nada a medio insertar.
"""
import random
import sys
import psycopg2
from psycopg2.extras import execute_values

CAJA_DSN = dict(dbname="CAJA", user="postgres", password="postgres", host="127.0.0.1", port=5432)
TALLER_DSN = dict(dbname="TALLER", user="postgres", password="postgres", host="127.0.0.1", port=5432)

DEPOSITOS_POR_SUCURSAL = [
    "BAZAR", "CARNICERIA", "PANADERIA", "CONFITERIA",
    "PATIO DE COMIDAS", "POLLERIA", "FIAMBRERIA", "SALA",
]
SUCURSALES_NUEVAS = ["LUQUE", "ASUNCION-ROYAL"]

MAPA_UNIDAD = {"UN": 3, "KG": 1, "CJ": 5, "LT": 3}  # -> id_unidad_medida
MAPA_IVA = {10: 2, 5: 3, 0: 4, 15: 1}  # pct_iva -> id_tipo_impuesto

BATCH = 5000


def log(msg):
    print(msg, flush=True)


def asegurar_sucursales(cur):
    cur.execute("SELECT id_sucursal, upper(trim(descripcion)) FROM sucursal")
    existentes = {desc: sid for sid, desc in cur.fetchall()}
    ids = dict(existentes)
    for nombre in SUCURSALES_NUEVAS:
        if nombre in existentes:
            continue
        cur.execute(
            "INSERT INTO sucursal (descripcion, activo) VALUES (%s, true) RETURNING id_sucursal",
            (nombre,),
        )
        nid = cur.fetchone()[0]
        ids[nombre] = nid
        log(f"  + sucursal creada: {nombre} (id={nid})")
    return ids  # nombre_upper -> id_sucursal


def asegurar_depositos(cur, sucursal_ids):
    cur.execute("SELECT id_deposito, id_sucursal, upper(trim(descripcion)) FROM deposito")
    existentes = {(sid, desc): did for did, sid, desc in cur.fetchall()}
    ids = dict(existentes)
    for nombre_suc, id_suc in sucursal_ids.items():
        for cat in DEPOSITOS_POR_SUCURSAL:
            clave = (id_suc, cat)
            if clave in ids:
                continue
            cur.execute(
                "INSERT INTO deposito (descripcion, id_sucursal, activo) VALUES (%s, %s, true) "
                "RETURNING id_deposito",
                (cat, id_suc),
            )
            did = cur.fetchone()[0]
            ids[clave] = did
            log(f"  + deposito creado: {cat} en {nombre_suc} (id={did})")
    return ids  # (id_sucursal, CATEGORIA) -> id_deposito


def cargar_precios(cur_caja):
    """Para cada cod_articulo: mejor precio de lista 2, o si no hay, el más
    reciente de cualquier lista. Devuelve {cod_articulo: (precio, sigla_venta)}."""
    mejor_lista2 = {}
    mejor_cualquiera = {}
    cur_caja.execute(
        "SELECT cod_articulo, cod_lista, sigla_venta, precio_venta, fec_vigencia FROM preciosartlocal"
    )
    while True:
        filas = cur_caja.fetchmany(50000)
        if not filas:
            break
        for cod, lista, sigla, precio, fecha in filas:
            actual = mejor_cualquiera.get(cod)
            if actual is None or fecha > actual[2]:
                mejor_cualquiera[cod] = (precio, sigla, fecha)
            if lista == 2:
                actual2 = mejor_lista2.get(cod)
                if actual2 is None or fecha > actual2[2]:
                    mejor_lista2[cod] = (precio, sigla, fecha)
    resultado = {}
    for cod, (precio, sigla, _f) in mejor_cualquiera.items():
        resultado[cod] = (precio, sigla)
    for cod, (precio, sigla, _f) in mejor_lista2.items():
        resultado[cod] = (precio, sigla)
    return resultado


def main():
    con_caja = psycopg2.connect(**CAJA_DSN)
    con_taller = psycopg2.connect(**TALLER_DSN)
    try:
        cur_caja = con_caja.cursor()
        cur_taller = con_taller.cursor()

        log("1) Asegurando sucursales y depositos...")
        sucursal_ids = asegurar_sucursales(cur_taller)
        deposito_ids = asegurar_depositos(cur_taller, sucursal_ids)
        con_taller.commit()

        ids_sala = {
            nombre: deposito_ids[(sid, "SALA")]
            for nombre, sid in sucursal_ids.items()
        }
        log(f"  depositos SALA: {ids_sala}")

        log("2) Cargando precios de CAJA (preciosartlocal)...")
        precios = cargar_precios(cur_caja)
        log(f"  {len(precios)} articulos con precio encontrado")

        log("3) Leyendo item_code existentes en TALLER...")
        cur_taller.execute("SELECT item_code FROM item")
        codigos_existentes = {r[0] for r in cur_taller.fetchall()}

        log("4) Leyendo articulolocal de CAJA...")
        cur_caja.execute(
            "SELECT cod_articulo, descripcion, pct_iva, hab_venta FROM articulolocal ORDER BY cod_articulo"
        )
        articulos = cur_caja.fetchall()
        log(f"  {len(articulos)} articulos a importar")

        log("5) Insertando en item + stock (una sola transaccion)...")
        insert_item_sql = """
            INSERT INTO item (item_code, descripcion, unidad_med, activo,
                               id_tipo_impuesto, precio_unitario, id_proveedor,
                               id_tipo_item, cantidad_minima)
            VALUES %s
            RETURNING id_item, item_code
        """
        insert_stock_sql = """
            INSERT INTO stock (id_sucursal, id_deposito, id_item, cantidad)
            VALUES %s
        """

        total_items = 0
        total_stock = 0
        for i in range(0, len(articulos), BATCH):
            lote = articulos[i:i + BATCH]
            filas_item = []
            for cod, desc, pct_iva, hab_venta in lote:
                item_code = str(cod)
                if item_code in codigos_existentes:
                    item_code = f"{cod}-CAJA"
                codigos_existentes.add(item_code)

                precio, sigla = precios.get(cod, (None, None))
                unidad_med = MAPA_UNIDAD.get(sigla)
                id_tipo_impuesto = MAPA_IVA.get(int(pct_iva)) if pct_iva is not None else None
                activo = (hab_venta == "S")
                precio_unitario = precio if precio is not None else 0

                rnd = random.Random(cod)
                if unidad_med == 1:  # Kilogramo
                    cantidad_minima = rnd.randint(1, 5)
                elif unidad_med == 5:  # Paquete
                    cantidad_minima = rnd.randint(2, 10)
                else:
                    cantidad_minima = rnd.randint(5, 20)

                filas_item.append((
                    item_code, desc.strip(), unidad_med, activo,
                    id_tipo_impuesto, precio_unitario, None, None, cantidad_minima,
                ))

            resultados = execute_values(cur_taller, insert_item_sql, filas_item, fetch=True)
            total_items += len(resultados)

            filas_stock = []
            for (id_item, _item_code), (cod, *_resto) in zip(resultados, lote):
                for nombre_suc, id_deposito in ids_sala.items():
                    rnd = random.Random((cod, nombre_suc))
                    cantidad = rnd.randint(0, 150)
                    filas_stock.append((
                        sucursal_ids[nombre_suc], id_deposito, id_item, cantidad,
                    ))
            execute_values(cur_taller, insert_stock_sql, filas_stock)
            total_stock += len(filas_stock)

            log(f"  ... {total_items}/{len(articulos)} items, {total_stock} filas de stock")

        con_taller.commit()
        log(f"OK: {total_items} items y {total_stock} filas de stock insertadas y confirmadas.")
    except Exception:
        con_taller.rollback()
        log("ERROR: se hizo rollback, no se guardo nada.")
        raise
    finally:
        con_caja.close()
        con_taller.close()


if __name__ == "__main__":
    sys.exit(main())
