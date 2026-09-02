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
            , u.usu_email
            , CONCAT(p.nombres, ' ', p.apellidos)nombre_persona
            , g.gru_des grupo
        FROM
            usuarios u
        left join
            personas p on p.id_persona = u.fun_id
        left join
            grupos g ON g.gru_id = u.gru_id
        WHERE
            u.usu_nick = %s
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
                        , "usu_email": usuario_encontrado[7]
                        , "nombre_persona": usuario_encontrado[8]
                        , "grupo": usuario_encontrado[9]
                    }  # Retornar los datos de la usuario
            else:
                return None # Retornar None si no se encuentra el usuario
        except Exception as e:
            app.logger.error(f"Error al obtener usuario: {str(e)}")
            return None

        finally:
            cur.close()
            con.close()

    def registrarIntentoFallido(self, usu_id: int, intentos_maximos: int) -> int:
        """Incrementa el contador de intentos fallidos; si llega al máximo, bloquea el usuario.
        Devuelve el nuevo contador de intentos (0 si ocurrió un error)."""
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                UPDATE usuarios
                SET usu_nro_intentos = usu_nro_intentos + 1
                WHERE usu_id = %s
                RETURNING usu_nro_intentos
            """, (usu_id,))
            nuevo_intentos = cur.fetchone()[0]
            if nuevo_intentos >= intentos_maximos:
                cur.execute("UPDATE usuarios SET usu_estado = false WHERE usu_id = %s", (usu_id,))
            con.commit()
            return nuevo_intentos
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al registrar intento fallido: {str(e)}")
            return 0
        finally:
            cur.close()
            con.close()

    def resetearIntentos(self, usu_id: int):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("UPDATE usuarios SET usu_nro_intentos = 0 WHERE usu_id = %s", (usu_id,))
            con.commit()
        except Exception as e:
            con.rollback()
            app.logger.error(f"Error al resetear intentos: {str(e)}")
        finally:
            cur.close()
            con.close()

    def buscarUsuarioPorId(self, usu_id: int):

        buscar_usuario_sql = """
        SELECT
            u.usu_id
            , TRIM(u.usu_nick) nick
            , u.usu_email
            , CONCAT(p.nombres, ' ', p.apellidos)nombre_persona
            , g.gru_des grupo
        FROM
            usuarios u
        left join
            personas p on p.id_persona = u.fun_id
        left join
            grupos g ON g.gru_id = u.gru_id
        WHERE
            u.usu_id = %s AND u.usu_estado is true
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(buscar_usuario_sql, (usu_id,))
            usuario_encontrado = cur.fetchone()
            if usuario_encontrado:
                return {
                        "usu_id": usuario_encontrado[0]
                        , "usu_nick": usuario_encontrado[1]
                        , "usu_email": usuario_encontrado[2]
                        , "nombre_persona": usuario_encontrado[3]
                        , "grupo": usuario_encontrado[4]
                    }
            else:
                return None
        except Exception as e:
            app.logger.error(f"Error al obtener usuario por id: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()