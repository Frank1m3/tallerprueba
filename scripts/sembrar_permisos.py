"""Siembra (idempotente) los módulos, ventanas y permisos por grupo.

Las ventanas se arman a partir de los endpoints reales del menú, así la ruta
de cada una siempre coincide con las rutas registradas en la aplicación.
Ejecutar:  python scripts/sembrar_permisos.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.conexion.Conexion import Conexion

COMPRAS_API = '/api/v1/gestionar-compras'

# (módulo, nombre de la ventana, endpoint del menú, prefijo de su API)
VENTANAS = [
    ('Referenciales', 'Ciudad',            'ciudad.ciudadIndex',                '/api/v1/ciudades'),
    ('Referenciales', 'País',              'pais.paisIndex',                    '/api/v1/paises'),
    ('Referenciales', 'Nacionalidad',      'nacionalidad.nacionalidadIndex',    '/api/v1/nacionalidades'),
    ('Referenciales', 'Personas',          'persona.personaIndex',              '/api/v1/personas'),
    ('Referenciales', 'Sexo',              'sexo.sexoIndex',                    '/api/v1/sexos'),
    ('Referenciales', 'Sucursales',        'sucursal.sucursalIndex',            '/api/v1/sucursales'),
    ('Referenciales', 'Depósitos',         'deposito.depositoIndex',            '/api/v1/depositos'),
    ('Referenciales', 'Estado civil',      'estado_civil.estado_civilIndex',      '/api/v1/estadosciviles'),
    ('Referenciales', 'Proveedores',       'proveedor.proveedorIndex',          '/api/v1/proveedores'),
    ('Referenciales', 'Items / Productos', 'item.itemIndex',                    '/api/v1/item'),
    ('Referenciales', 'Tipo de Item',      'tipoitem.tipoItemIndex',            '/api/v1/tipo_item'),
    ('Referenciales', 'Grupos de items',   'grupo.grupoIndex',                  '/api/v1/grupos'),
    ('Referenciales', 'Marcas',            'marca.marcaIndex',                  '/api/v1/marcas'),
    ('Referenciales', 'Unidad de Medida',  'unidadmedida.unidadMedidaIndex',    '/api/v1/unidad_medida'),
    ('Referenciales', 'Tipo de Impuesto',  'tipoimpuesto.tipoImpuestoIndex',    '/api/v1/tipo_impuesto'),
    ('Referenciales', 'Monedas',           'moneda.monedaIndex',                '/api/v1/monedas'),
    ('Referenciales', 'Formas de Pago',    'formapago.formasPagoIndex',         '/api/v1/formas_pago'),
    ('Referenciales', 'Clientes',          'cliente.clienteIndex',              '/api/v1/clientes'),
    ('Referenciales', 'Marcas de Tarjeta', 'marcatarjeta.marcaTarjetaIndex',    '/api/v1/marca_tarjeta'),
    ('Referenciales', 'Entidades Emisoras','entidademisora.entidadEmisoraIndex','/api/v1/entidad_emisora'),
    ('Ventas',        'Apertura de caja',  'apertura.aperturaIndex',            '/api/v1/aperturas'),
    ('Ventas',        'Punto de Venta',    'ventamod.ventaPos',                 '/api/v1/ventas'),
    ('Ventas',        'Arqueo de Caja',    'arqueomod.arqueo_index',            '/api/v1/arqueo'),
    ('Ventas',        'Cierre de caja',    'cierre.cierreIndex',                '/api/v1/cierres'),
    ('Compras',       'Solicitud de compra','solmod.solicitud_index',           f'{COMPRAS_API}/registrar-solicitud-compras'),
    ('Compras',       'Presupuesto',       'presumod.presupuesto_index',        f'{COMPRAS_API}/registrar-presupuesto'),
    ('Compras',       'Pedido de compra',  'pdcmod.pedidos_index',              f'{COMPRAS_API}/registrar-pedido-compras'),
    ('Compras',       'Orden de compra',   'ocmod.ordenes_index',               f'{COMPRAS_API}/registrar-orden-compras'),
    ('Compras',       'Recepción de mercaderías','rm_mod.recepcion_mercaderia', f'{COMPRAS_API}/recepcion-mercaderias'),
    ('Compras',       'Facturas de compra','facmod.facturas_index',             f'{COMPRAS_API}/registrar-factura-compras'),
    ('Producción',    'Etapas de Producción','tipoetapas.tipoEtapasIndex',      '/api/v1/tipo_etapas'),
    ('Producción',    'Parámetros de Calidad','parametrocalidad.parametroCalidadIndex','/api/v1/parametro_calidad'),
    ('Producción',    'Motivos de Ajuste', 'motivoajuste.motivoAjusteIndex',    '/api/v1/motivo_ajuste'),
]

# Ventanas cuyo blueprint comparte prefijo con otras: se usa la ruta completa
RUTA_COMPLETA = {'ventamod.ventaPos', 'arqueomod.arqueo_index'}

# permisos por grupo: (leer, insertar, editar, borrar) según módulo
PERFILES = {
    'administradores': lambda mod: (True, True, True, True),
    # ve todo; en Compras agrega y modifica pero NO anula/elimina
    'compras':         lambda mod: (True, True, True, False) if mod == 'Compras' else (True, False, False, False),
    # fiscal / auditor: solo consulta
    'fiscales':        lambda mod: (True, False, False, False),
}


def ruta_de(endpoint):
    for r in app.url_map.iter_rules():
        if r.endpoint == endpoint and 'GET' in r.methods:
            return r.rule
    raise SystemExit(f"Endpoint no encontrado en la aplicación: {endpoint}")


def main():
    con = Conexion().getConexion(); cur = con.cursor()
    try:
        # Reemplaza las filas de ejemplo originales (2 páginas de prueba sin uso)
        cur.execute("DELETE FROM permisos WHERE pag_id IN (SELECT pag_id FROM paginas WHERE pag_ruta IS NULL)")
        cur.execute("DELETE FROM paginas WHERE pag_ruta IS NULL")
        cur.execute("UPDATE modulos SET mod_des = 'Ventas' WHERE mod_id = 1 AND mod_des = 'caja'")
        for m in ('Referenciales', 'Ventas', 'Compras', 'Producción'):
            cur.execute("INSERT INTO modulos (mod_des) VALUES (%s) ON CONFLICT (mod_des) DO NOTHING", (m,))
        cur.execute("SELECT mod_des, mod_id FROM modulos"); mods = dict(cur.fetchall())
        cur.execute("SELECT gru_des, gru_id FROM grupos"); grupos = dict(cur.fetchall())

        for modulo, nombre, endpoint, api in VENTANAS:
            rule = ruta_de(endpoint)
            ruta = rule if endpoint in RUTA_COMPLETA else rule.rsplit('/', 1)[0]
            cur.execute("""
                INSERT INTO paginas (pag_nombre, pag_direcc, pag_estado, mod_id, pag_ruta, pag_api)
                VALUES (%s, %s, TRUE, %s, %s, %s)
                ON CONFLICT (pag_nombre) DO UPDATE
                    SET pag_direcc = EXCLUDED.pag_direcc, mod_id = EXCLUDED.mod_id,
                        pag_ruta = EXCLUDED.pag_ruta, pag_api = EXCLUDED.pag_api
                RETURNING pag_id
            """, (nombre, rule, mods[modulo], ruta, api))
            pag_id = cur.fetchone()[0]
            for grupo, regla in PERFILES.items():
                if grupo not in grupos:
                    continue
                leer, ins, edi, bor = regla(modulo)
                cur.execute("""
                    INSERT INTO permisos (pag_id, gru_id, leer, insertar, editar, borrar)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pag_id, gru_id) DO NOTHING
                """, (pag_id, grupos[grupo], leer, ins, edi, bor))
        con.commit()
        print(f"OK: {len(VENTANAS)} ventanas sembradas para {len(PERFILES)} grupos")
    except Exception:
        con.rollback(); raise
    finally:
        cur.close(); con.close()


if __name__ == '__main__':
    with app.app_context():
        main()
