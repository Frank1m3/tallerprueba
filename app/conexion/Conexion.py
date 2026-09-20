import psycopg2

class Conexion:

    """Metodo constructor
    """
    def __init__(self):
        # https://www.psycopg.org/docs/extensions.html#psycopg2.extensions.parse_dsn
        dbname = "TALLER"
        user = "postgres"
        password = "postgres"
        host = "127.0.0.1"
        port = 5432
        #self.con = psycopg2.connect("dbname=veterinaria-db user=juandba host=localhost password=admin")
        self.con = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        self._marcar_usuario_actual()

    # Propaga el usuario logueado (sesión de Flask) a la conexión de Postgres,
    # para que los triggers de auditoría sepan "quién" hizo cada operación.
    def _marcar_usuario_actual(self):
        try:
            from flask import session
            usuario = session.get('usuario_nombre') if session else None
        except RuntimeError:
            usuario = None  # fuera de un request (script suelto, migraciones, etc.)
        cur = self.con.cursor()
        cur.execute("SELECT set_config('myapp.usuario_actual', %s, false)", (usuario or 'sistema',))
        cur.close()

    """getConexion

        retorna la instancia de la base de datos
    """
    def getConexion(self):
        return self.con