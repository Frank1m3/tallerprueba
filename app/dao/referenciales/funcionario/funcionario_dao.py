from flask import current_app as app
from app.conexion.Conexion import Conexion

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
            creacion_hora
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
                'creacion_hora': str(e[7])
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
