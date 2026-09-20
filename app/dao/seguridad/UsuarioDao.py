from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2


class UsuarioDao:

    def listar(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT u.usu_id, TRIM(u.usu_nick), u.usu_email, u.gru_id, g.gru_des,
                       u.usu_estado, u.usu_nro_intentos, u.fun_id,
                       CONCAT(p.nombres, ' ', p.apellidos)
                FROM usuarios u
                LEFT JOIN grupos g ON g.gru_id = u.gru_id
                LEFT JOIN personas p ON p.id_persona = u.fun_id
                ORDER BY u.usu_id
            """)
            return [{"usu_id": r[0], "usu_nick": r[1], "usu_email": r[2], "gru_id": r[3], "grupo": r[4],
                     "usu_estado": r[5], "usu_nro_intentos": r[6], "fun_id": r[7],
                     "persona": (r[8] or '').strip()} for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def crear(self, nick, clave_hash, fun_id, gru_id, email):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO usuarios (usu_nick, usu_clave, usu_nro_intentos, fun_id, gru_id, usu_estado, usu_email)
                VALUES (%s, %s, 0, %s, %s, TRUE, %s) RETURNING usu_id
            """, (nick, clave_hash, fun_id, gru_id, email or None))
            nuevo = cur.fetchone()[0]
            con.commit()
            return nuevo, None
        except psycopg2.errors.UniqueViolation:
            con.rollback(); return None, 'Ya existe un usuario con ese nombre.'
        except psycopg2.errors.ForeignKeyViolation:
            con.rollback(); return None, 'El funcionario o el perfil seleccionado no existe.'
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al crear usuario: {e}")
            return None, 'No se pudo crear el usuario.'
        finally:
            cur.close(); con.close()

    def actualizar(self, usu_id, gru_id, email, estado):
        """Al reactivar un usuario (desbloqueo) se reinicia el contador de intentos fallidos."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                UPDATE usuarios
                SET gru_id = %s, usu_email = %s, usu_estado = %s,
                    usu_nro_intentos = CASE WHEN %s THEN 0 ELSE usu_nro_intentos END
                WHERE usu_id = %s
            """, (gru_id, email or None, estado, estado, usu_id))
            con.commit()
            return cur.rowcount > 0
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al actualizar usuario: {e}")
            return False
        finally:
            cur.close(); con.close()

    def nick(self, usu_id):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT TRIM(usu_nick) FROM usuarios WHERE usu_id = %s", (usu_id,))
            r = cur.fetchone()
            return r[0] if r else None
        finally:
            cur.close(); con.close()
