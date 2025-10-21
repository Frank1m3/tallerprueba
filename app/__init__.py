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
modulo_compras = '/gestionar-compras'
api_v1 = '/api/v1'

# ================================
# Importar y registrar blueprints de seguridad
# ================================
from app.rutas.seguridad.login_routes import logmod
app.register_blueprint(logmod)

# ================================
# Referenciales - Rutas
# ================================
from app.rutas.referenciales.ciudad.ciudad_routes import ciumod
from app.rutas.referenciales.pais.pais_routes import paismod
from app.rutas.referenciales.nacionalidad.nacionalidad_routes import nacmod
from app.rutas.referenciales.persona.persona_routes import permod
from app.rutas.referenciales.proveedor.proveedor_routes import provmod
from app.rutas.referenciales.cliente.cliente_routes import climod
from app.rutas.referenciales.sucursal.sucursal_routes import sucmod
from app.rutas.referenciales.deposito.deposito_routes import depomod
from app.rutas.referenciales.estado_civil.estado_civil_routes import estmod
from app.rutas.referenciales.sexo.sexo_routes import sexomod
from app.rutas.referenciales.marca.marca_routes import marcmod
from app.rutas.referenciales.forma_pago.forma_pago_routes import formapago_mod
from app.rutas.referenciales.apertura.apertura_routes import apermod

referenciales_rutas = [
    (ciumod, 'ciudad'), (paismod, 'pais'), (nacmod, 'nacionalidad'), (permod, 'persona'),
    (provmod, 'proveedor'), (climod, 'cliente'), (sucmod, 'sucursal'), (depomod, 'deposito'),
    (estmod, 'estado_civil'), (sexomod, 'sexo'), (marcmod, 'marca'), (apermod, 'apertura'),
    (formapago_mod, 'formas_pago')
]

for bp, path in referenciales_rutas:
    app.register_blueprint(bp, url_prefix=f'{modulo_referenciales}/{path}')

# ================================
# Referenciales - APIs
# ================================
from app.rutas.referenciales.ciudad.ciudad_api import ciuapi
from app.rutas.referenciales.pais.pais_api import paiapi
from app.rutas.referenciales.nacionalidad.nacionalidad_api import nacapi
from app.rutas.referenciales.persona.persona_api import perapi
from app.rutas.referenciales.proveedor.proveedor_api import provapi
from app.rutas.referenciales.cliente.cliente_api import cliapi
from app.rutas.referenciales.sucursal.sucursal_api import sucapi
from app.rutas.referenciales.deposito.deposito_api import depoapi
from app.rutas.referenciales.estado_civil.estado_civil_api import estadocivilapi
from app.rutas.referenciales.sexo.sexo_api import sexoapi
from app.rutas.referenciales.marca.marca_api import marcaapi
from app.rutas.referenciales.apertura.apertura_api import aperapi
from app.rutas.referenciales.forma_pago.forma_pago_api import forma_pago_api

referenciales_apis = [
    ciuapi, paiapi, nacapi, perapi, provapi, cliapi, sucapi,
    depoapi, estadocivilapi, sexoapi, marcaapi, aperapi, forma_pago_api
]

for api in referenciales_apis:
    app.register_blueprint(api, url_prefix=api_v1)

# ================================
# Gestionar Compras - Rutas
# ================================
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedidos_compras_routes import pdcmod
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_routes import solmod
from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_routes import presumod
from app.rutas.gestionar_compras.registrar_recepcion_compras.recepcion_mercaderia_routes import rm_mod

app.register_blueprint(pdcmod, url_prefix=f'{modulo_compras}/registrar-pedido-compras')
app.register_blueprint(solmod, url_prefix=f'{modulo_compras}/registrar-solicitud-compras')
app.register_blueprint(presumod, url_prefix=f'{modulo_compras}/registrar-presupuesto')
app.register_blueprint(rm_mod, url_prefix=f'{modulo_compras}/registrar-recepcion-compras')

# ================================
# Gestionar Compras - APIs
# ================================
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedido_compras_api import pdcapi
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_api import scapi
from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_api import presuapi
from app.rutas.gestionar_compras.registrar_recepcion_compras.recepcion_mercaderia_api import rm_api

app.register_blueprint(pdcapi, url_prefix=f'{api_v1}{modulo_compras}/registrar-pedido-compras')
app.register_blueprint(scapi, url_prefix=f'{api_v1}{modulo_compras}/registrar-solicitud-compras')
app.register_blueprint(presuapi, url_prefix=f'{api_v1}{modulo_compras}/registrar-presupuesto')
# Exento CSRF porque recibe JSON desde AJAX
app.register_blueprint(rm_api, url_prefix=f'{api_v1}{modulo_compras}/recepcion-mercaderias')

# ================================
# Cierre - Rutas y APIs
# ================================
from app.rutas.referenciales.cierre.cierre_routes import cierremod
from app.rutas.referenciales.cierre.cierre_api import cierreapi

app.register_blueprint(cierreapi, url_prefix=api_v1)
app.register_blueprint(cierremod, url_prefix=f'{modulo_referenciales}/cierre')
