from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2

class FuncionarioDao:

    def get_funcionarios(self):
        """
        Devuelve todos los funcionarios activos con:
        - fun_id
        - nombre_completo (nombres + apellidos)
        - ci (desde funcionarios)
        - estado, es_cajero, es_fiscal, fecha/hora de creación
        """
        sql = """
        SELECT
            fun_id,
            CONCAT(nombres, ' ', apellidos) AS nombre_completo,
            ci,
            fun_estado,
            es_cajero,
            es_fiscal,
            creacion_fecha,
            creacion_hora,
            nombres,
            apellidos
        FROM funcionarios
        WHERE fun_estado = TRUE
        ORDER BY fun_id
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            empleados = cur.fetchall()
            return [{
                'fun_id': e[0],
                'nombre_completo': e[1],
                'ci': e[2],
                'estado': e[3],
                'es_cajero': e[4],
                'es_fiscal': e[5],
                'creacion_fecha': str(e[6]),
                'creacion_hora': str(e[7]),
                'nombres': e[8] or '',
                'apellidos': e[9] or ''
            } for e in empleados]
        except Exception as e:
            app.logger.error(f"Error al obtener funcionarios: {str(e)}")
            return []
        finally:
            cur.close()
            con.close()

    def get_funcionario_by_id(self, fun_id):
        """
        Devuelve los datos de un funcionario por su ID
        """
        sql = """
        SELECT
            fun_id,
            CONCAT(nombres, ' ', apellidos) AS nombre_completo,
            ci,
            fun_estado,
            es_cajero,
            es_fiscal,
            creacion_fecha,
            creacion_hora
        FROM funcionarios
        WHERE fun_id = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (fun_id,))
            f = cur.fetchone()
            if f:
                return {
                    'fun_id': f[0],
                    'nombre_completo': f[1],
                    'ci': f[2],
                    'estado': f[3],
                    'es_cajero': f[4],
                    'es_fiscal': f[5],
                    'creacion_fecha': str(f[6]),
                    'creacion_hora': str(f[7])
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener funcionario por ID: {str(e)}")
            return None
        finally:
            cur.close()
            con.close()

    def get_cargos(self):
        """Cargos disponibles (para dar de alta un funcionario nuevo)."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT car_id, car_des FROM cargos ORDER BY car_des")
            return [{'car_id': r[0], 'car_des': r[1]} for r in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener cargos: {str(e)}")
            return []
        finally:
            cur.close(); con.close()

    def crear(self, nombres, apellidos, ci, car_id, creado_por):
        """Da de alta una persona nueva y su ficha de funcionario (fun_id == id_persona).
        Se usa cuando, al crear un usuario del sistema, la persona todavía no está
        cargada como funcionario. Devuelve (fun_id, error)."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO personas (nombres, apellidos, ci, creacion_fecha, creacion_hora, creacion_usuario)
                VALUES (%s, %s, %s, CURRENT_DATE, CURRENT_TIME, %s) RETURNING id_persona
            """, (nombres, apellidos, ci, creado_por))
            id_persona = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO funcionarios (fun_id, car_id, fun_estado, creacion_fecha, creacion_hora,
                                          creacion_usuario, es_cajero, es_fiscal, nombres, apellidos, ci)
                VALUES (%s, %s, TRUE, CURRENT_DATE, CURRENT_TIME, %s, FALSE, FALSE, %s, %s, %s)
            """, (id_persona, car_id, creado_por, nombres, apellidos, ci))
            con.commit()
            return id_persona, None
        except psycopg2.errors.UniqueViolation:
            con.rollback(); return None, 'Ya existe una persona registrada con esa cédula.'
        except psycopg2.errors.ForeignKeyViolation:
            con.rollback(); return None, 'El cargo seleccionado no existe.'
        except psycopg2.Error as e:
            con.rollback(); app.logger.error(f"Error al crear funcionario: {e}")
            return None, 'No se pudo crear el funcionario.'
        finally:
            cur.close(); con.close()

    def cambiar_estado_funcionario(self, fun_id, estado):
        """
        Cambia el estado activo/inactivo del funcionario
        """
        sql = "UPDATE funcionarios SET fun_estado=%s WHERE fun_id=%s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (estado, fun_id))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al cambiar estado del funcionario: {str(e)}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()
