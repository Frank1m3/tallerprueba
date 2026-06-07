from datetime import timedelta
from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# ================================
# Configuración básica
# ================================
app.secret_key = b'_5#y2L"F6Q7z\n\xec]/'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Inicializar CSRF
csrf = CSRFProtect(app)

# ================================
# Variables de rutas comunes
# ================================
modulo_referenciales = '/referenciales'
modulo_compras       = '/gestionar-compras'
modulo_ventas        = '/gestionar-ventas'
api_v1               = '/api/v1'

# ================================
# Seguridad
# ================================
from app.rutas.seguridad.login_routes import logmod
app.register_blueprint(logmod)

# ================================
# Referenciales - Rutas
# ================================
from app.rutas.referenciales.ciudad.ciudad_routes             import ciumod
from app.rutas.referenciales.pais.pais_routes                 import paismod
from app.rutas.referenciales.nacionalidad.nacionalidad_routes import nacmod
from app.rutas.referenciales.persona.persona_routes           import permod
from app.rutas.referenciales.proveedor.proveedor_routes       import provmod
from app.rutas.referenciales.cliente.cliente_routes           import climod
from app.rutas.referenciales.sucursal.sucursal_routes         import sucmod
from app.rutas.referenciales.deposito.deposito_routes         import depomod
from app.rutas.referenciales.estado_civil.estado_civil_routes import estmod
from app.rutas.referenciales.sexo.sexo_routes                 import sexomod
from app.rutas.referenciales.marca.marca_routes               import marcmod
from app.rutas.referenciales.forma_pago.forma_pago_routes     import formapago_mod
from app.rutas.referenciales.apertura.apertura_routes         import apermod
# --- Nuevas referenciales de compras ---
from app.rutas.referenciales.tipo_item.tipo_item_routes         import tipoitem_mod
from app.rutas.referenciales.tipo_impuesto.tipo_impuesto_routes import tipoimpuesto_mod
from app.rutas.referenciales.grupo.grupo_routes                 import grupo_mod
from app.rutas.referenciales.moneda.moneda_routes               import moneda_mod
from app.rutas.referenciales.unidad_medida.unidad_medida_routes import unidadmedida_mod
from app.rutas.referenciales.item.item_routes                   import item_mod
# --- Nuevas referenciales de ventas ---
from app.rutas.referenciales.marca_tarjeta.marca_tarjeta_routes     import marcatarjeta_mod
from app.rutas.referenciales.entidad_emisora.entidad_emisora_routes import entidademisora_mod
# --- Nuevas referenciales de producción ---
from app.rutas.referenciales.motivo_ajuste.motivo_ajuste_routes         import motivoajuste_mod
from app.rutas.referenciales.tipo_etapas.tipo_etapas_routes             import tipoetapas_mod
from app.rutas.referenciales.parametro_calidad.parametro_calidad_routes import parametrocalidad_mod

referenciales_rutas = [
    (ciumod,       'ciudad'),
    (paismod,      'pais'),
    (nacmod,       'nacionalidad'),
    (permod,       'persona'),
    (provmod,      'proveedor'),
    (climod,       'cliente'),
    (sucmod,       'sucursal'),
    (depomod,      'deposito'),
    (estmod,       'estado_civil'),
    (sexomod,      'sexo'),
    (marcmod,      'marca'),
    (apermod,      'apertura'),
    (formapago_mod,'formas_pago'),
    # --- Nuevas referenciales de compras ---
    (tipoitem_mod,     'tipo_item'),
    (tipoimpuesto_mod, 'tipo_impuesto'),
    (grupo_mod,        'grupo'),
    (moneda_mod,       'moneda'),
    (unidadmedida_mod, 'unidad_medida'),
    (item_mod,         'item'),
    # --- Nuevas referenciales de ventas ---
    (marcatarjeta_mod,   'marca_tarjeta'),
    (entidademisora_mod, 'entidad_emisora'),
    # --- Nuevas referenciales de producción ---
    (motivoajuste_mod,     'motivo_ajuste'),
    (tipoetapas_mod,       'tipo_etapas'),
    (parametrocalidad_mod, 'parametro_calidad'),
]

for bp, path in referenciales_rutas:
    app.register_blueprint(bp, url_prefix=f'{modulo_referenciales}/{path}')

# ================================
# Referenciales - APIs
# ================================
from app.rutas.referenciales.ciudad.ciudad_api             import ciuapi
from app.rutas.referenciales.pais.pais_api                 import paiapi
from app.rutas.referenciales.nacionalidad.nacionalidad_api import nacapi
from app.rutas.referenciales.persona.persona_api           import perapi
from app.rutas.referenciales.proveedor.proveedor_api       import provapi
from app.rutas.referenciales.cliente.cliente_api           import cliapi
from app.rutas.referenciales.sucursal.sucursal_api         import sucapi
from app.rutas.referenciales.deposito.deposito_api         import depoapi
from app.rutas.referenciales.estado_civil.estado_civil_api import estadocivilapi
from app.rutas.referenciales.sexo.sexo_api                 import sexoapi
from app.rutas.referenciales.marca.marca_api               import marcaapi
from app.rutas.referenciales.apertura.apertura_api         import aperapi
from app.rutas.referenciales.forma_pago.forma_pago_api     import forma_pago_api
# --- Nuevas referenciales de compras ---
from app.rutas.referenciales.tipo_item.tipo_item_api         import tipo_item_api
from app.rutas.referenciales.tipo_impuesto.tipo_impuesto_api import tipo_impuesto_api
from app.rutas.referenciales.grupo.grupo_api                 import grupo_api
from app.rutas.referenciales.moneda.moneda_api               import moneda_api
from app.rutas.referenciales.unidad_medida.unidad_medida_api import unidad_medida_api
from app.rutas.referenciales.item.item_api                   import item_api
# --- Nuevas referenciales de ventas ---
from app.rutas.referenciales.marca_tarjeta.marca_tarjeta_api     import marca_tarjeta_api
from app.rutas.referenciales.entidad_emisora.entidad_emisora_api import entidad_emisora_api
# --- Nuevas referenciales de producción ---
from app.rutas.referenciales.motivo_ajuste.motivo_ajuste_api         import motivo_ajuste_api
from app.rutas.referenciales.tipo_etapas.tipo_etapas_api             import tipo_etapas_api
from app.rutas.referenciales.parametro_calidad.parametro_calidad_api import parametro_calidad_api

referenciales_apis = [
    ciuapi, paiapi, nacapi, perapi, provapi, cliapi, sucapi,
    depoapi, estadocivilapi, sexoapi, marcaapi, aperapi, forma_pago_api,
    # --- Nuevas referenciales de compras ---
    tipo_item_api, tipo_impuesto_api, grupo_api,
    moneda_api, unidad_medida_api, item_api,
    # --- Nuevas referenciales de ventas ---
    marca_tarjeta_api, entidad_emisora_api,
    # --- Nuevas referenciales de producción ---
    motivo_ajuste_api, tipo_etapas_api, parametro_calidad_api,
]

for api in referenciales_apis:
    app.register_blueprint(api, url_prefix=api_v1)

# ================================
# Gestionar Compras - Rutas
# ================================
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedidos_compras_routes  import pdcmod
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_routes import solmod
from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_routes         import presumod
from app.rutas.gestionar_compras.registrar_recepcion_compras.recepcion_mercaderia_routes    import rm_mod

app.register_blueprint(pdcmod,   url_prefix=f'{modulo_compras}/registrar-pedido-compras')
app.register_blueprint(solmod,   url_prefix=f'{modulo_compras}/registrar-solicitud-compras')
app.register_blueprint(presumod, url_prefix=f'{modulo_compras}/registrar-presupuesto')
app.register_blueprint(rm_mod,   url_prefix=f'{modulo_compras}/registrar-recepcion-compras')

# ================================
# Gestionar Compras - APIs
# ================================
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedido_compras_api      import pdcapi
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_api import scapi
from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_api            import presuapi
from app.rutas.gestionar_compras.registrar_recepcion_compras.recepcion_mercaderia_api       import rm_api

app.register_blueprint(pdcapi,    url_prefix=f'{api_v1}{modulo_compras}/registrar-pedido-compras')
app.register_blueprint(scapi,     url_prefix=f'{api_v1}{modulo_compras}/registrar-solicitud-compras')
app.register_blueprint(presuapi,  url_prefix=f'{api_v1}{modulo_compras}/registrar-presupuesto')
app.register_blueprint(rm_api,    url_prefix=f'{api_v1}{modulo_compras}/recepcion-mercaderias')

# ================================
# Cierre - Rutas y APIs
# ================================
from app.rutas.referenciales.cierre.cierre_routes import cierremod
from app.rutas.referenciales.cierre.cierre_api    import cierreapi

app.register_blueprint(cierremod, url_prefix=f'{modulo_referenciales}/cierre')
app.register_blueprint(cierreapi, url_prefix=api_v1)

# ================================
# Gestionar Ventas - Rutas
# ================================
from app.rutas.gestionar_ventas.ventapos.venta_routes import ventamod

app.register_blueprint(ventamod, url_prefix=f'{modulo_ventas}')

# ================================
# Gestionar Ventas - APIs
# ================================
from app.rutas.gestionar_ventas.ventapos.ventapos_api import ventaapi

app.register_blueprint(ventaapi, url_prefix=api_v1)

# ================================
# Arqueo de Caja - Rutas y API
# ================================
from app.rutas.gestionar_ventas.arqueo.arqueo_routes import arqueomod
from app.rutas.gestionar_ventas.arqueo.arqueo_api    import arqueoapi

app.register_blueprint(arqueomod, url_prefix=f'{modulo_ventas}')
app.register_blueprint(arqueoapi, url_prefix=api_v1)