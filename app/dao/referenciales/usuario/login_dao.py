# Data access object - DAO
from flask import current_app as app
from app.conexion.Conexion import Conexion

class LoginDao:

    def buscarUsuario(self, usu_nick: str):

        buscar_usuario_sql = """
        SELECT
            u.usu_id
            , TRIM(u.usu_nick) nick
            , u.usu_clave
            , u.usu_nro_intentos
            , u.fun_id
            , u.gru_id
            , u.usu_estado
            , CONCAT(p.nombres, ' ', p.apellidos)nombre_persona
            , g.gru_des grupo
        FROM
            usuarios u
        left join
            personas p on p.id_persona = u.fun_id
        left join
            grupos g ON g.gru_id = u.gru_id
        WHERE
            u.usu_nick = %s AND u.usu_estado is true
        """
        # objeto conexion
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(buscar_usuario_sql, (usu_nick,))
            usuario_encontrado = cur.fetchone() # Obtener una sola fila
            if usuario_encontrado:
                return {
                        "usu_id": usuario_encontrado[0]
                        , "usu_nick": usuario_encontrado[1]
                        , "usu_clave": usuario_encontrado[2]
                        , "usu_nro_intentos": usuario_encontrado[3]
                        , "fun_id": usuario_encontrado[4]
                        , "gru_id": usuario_encontrado[5]
                        , "usu_estado": usuario_encontrado[6]
                        , "nombre_persona": usuario_encontrado[7]
                        , "grupo": usuario_encontrado[8]
                    }  # Retornar los datos de la usuario
            else:
                return None # Retornar None si no se encuentra el usuario
        except Exception as e:
            app.logger.error(f"Error al obtener usuario: {str(e)}")
            return None

        finally:
            cur.close()
            con.close()