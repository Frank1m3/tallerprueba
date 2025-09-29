from datetime import timedelta
from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# Inicializar secret key y configuración ANTES de CSRF
app.secret_key = b'_5#y2L"F6Q7z\n\xec]/'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Crear la instancia csrf y asociarla a la app
csrf = CSRFProtect(app)


# importar modulo de seguridad
from app.rutas.seguridad.login_routes import logmod
app.register_blueprint(logmod)

# importar referenciales
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

# importar gestionar compras
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedidos_compras_routes \
    import pdcmod

# registro de modulos - gestionar compras
modulo1 = '/gestionar-compras'
app.register_blueprint(pdcmod, url_prefix=f'{modulo1}/registrar-pedido-compras')

# registrar referenciales
modulo0 = '/referenciales'
app.register_blueprint(ciumod, url_prefix=f'{modulo0}/ciudad')
app.register_blueprint(paismod, url_prefix=f'{modulo0}/pais')
app.register_blueprint(nacmod, url_prefix=f'{modulo0}/nacionalidad')
app.register_blueprint(permod, url_prefix=f'{modulo0}/persona')
app.register_blueprint(provmod, url_prefix=f'{modulo0}/proveedor')
app.register_blueprint(climod, url_prefix=f'{modulo0}/cliente')
app.register_blueprint(sucmod, url_prefix=f'{modulo0}/sucursal')
app.register_blueprint(depomod, url_prefix=f'{modulo0}/deposito')
app.register_blueprint(estmod, url_prefix=f'{modulo0}/estado_civil')
app.register_blueprint(sexomod, url_prefix=f'{modulo0}/sexo')
app.register_blueprint(marcmod, url_prefix=f'{modulo0}/marca')
app.register_blueprint(apermod, url_prefix=f'{modulo0}/apertura')
app.register_blueprint(formapago_mod, url_prefix=f'{modulo0}/formas_pago')

# APIS v1
from app.rutas.referenciales.ciudad.ciudad_api import ciuapi
from app.rutas.referenciales.apertura.apertura_api import aperapi

from app.rutas.referenciales.pais.pais_api import paiapi

from app.rutas.referenciales.nacionalidad.nacionalidad_api import nacapi

from app.rutas.referenciales.persona.persona_api import perapi

from app.rutas.referenciales.proveedor.proveedor_api import provapi

from app.rutas.referenciales.cliente.cliente_api import cliapi

from app.rutas.referenciales.sucursal.sucursal_api import sucapi

from app.rutas.referenciales.forma_pago.forma_pago_api import forma_pago_api

from app.rutas.referenciales.deposito.deposito_api import depoapi

from app.rutas.referenciales.estado_civil.estado_civil_api import estadocivilapi

from app.rutas.referenciales.sexo.sexo_api import sexoapi

from app.rutas.referenciales.marca.marca_api import marcaapi
from app.rutas.gestionar_compras.registrar_pedido_compras.registrar_pedido_compras_api \
    import pdcapi

apiversion1 = '/api/v1'
app.register_blueprint(ciuapi, url_prefix=apiversion1)
app.register_blueprint(paiapi, url_prefix=apiversion1)
app.register_blueprint(nacapi, url_prefix=apiversion1)
app.register_blueprint(perapi, url_prefix=apiversion1)
app.register_blueprint(provapi, url_prefix=apiversion1)
app.register_blueprint(cliapi, url_prefix=apiversion1)
app.register_blueprint(sucapi, url_prefix=apiversion1)
app.register_blueprint(depoapi, url_prefix=apiversion1)
app.register_blueprint(estadocivilapi, url_prefix=apiversion1)
app.register_blueprint(sexoapi, url_prefix=apiversion1)
app.register_blueprint(marcaapi, url_prefix=apiversion1)
app.register_blueprint(aperapi, url_prefix=apiversion1)
app.register_blueprint(forma_pago_api, url_prefix=apiversion1)
app.register_blueprint(pdcapi, url_prefix=f'{apiversion1}/{modulo1}/registrar-pedido-compras')

# importar rutas y apis de cierre
from app.rutas.referenciales.cierre.cierre_routes import cierremod
from app.rutas.referenciales.cierre.cierre_api import cierreapi

# registrar blueprint de cierre
app.register_blueprint(cierreapi, url_prefix=apiversion1)
app.register_blueprint(cierremod, url_prefix=f'{modulo0}/cierre')
# importar gestionar compras - solicitudes
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_routes import solmod
from app.rutas.gestionar_compras.registrar_solicitud_compras.registrar_solicitud_compras_api import scapi


# registrar blueprint de solicitudes
modulo1 = '/gestionar-compras'
app.register_blueprint(solmod, url_prefix=f'{modulo1}/registrar-solicitud-compras')
app.register_blueprint(scapi, url_prefix=f'/api/v1{modulo1}/registrar-solicitud-compras')

from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_api import presuapi
app.register_blueprint(presuapi, url_prefix='/api/v1/gestionar-compras/registrar-presupuesto')
from app.rutas.gestionar_compras.registrar_presupuesto.registrar_presupuesto_routes import presumod
app.register_blueprint(presumod, url_prefix='/gestionar-compras/registrar-presupuesto')
