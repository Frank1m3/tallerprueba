from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2
from psycopg2 import errors
from datetime import datetime

class PersonaDao:

    def _parse_fecha(self, fecha_str):
        """Convierte una fecha string a objeto date. Acepta dd/mm/yyyy o yyyy-mm-dd."""
        if not fecha_str:
            return None
        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
        for fmt in formatos:
            try:
                return datetime.strptime(str(fecha_str).strip(), fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha inválido: {fecha_str}")

    def _validar_sexo(self, sexo):
        """Valida y normaliza el sexo ('M' o 'F')."""
        if not sexo:
            return None
        sexo = str(sexo).strip().upper()
        if sexo in ['M', 'F']:
            return sexo
        if sexo.startswith('M'):
            return 'M'
        if sexo.startswith('F'):
            return 'F'
        raise ValueError(f"Valor de sexo inválido: {sexo}")

    def getPersonas(self):
        sql = """
        SELECT id_persona, fun_id, nombres, apellidos, ci,
               to_char(fechanac, 'YYYY-MM-DD') AS fechanac, sexo
        FROM personas
        ORDER BY id_persona
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            return [
                {
                    "id_persona": r[0],
                    "fun_id": r[1],
                    "nombres": r[2],
                    "apellidos": r[3],
                    "ci": r[4],
                    "fechanac": r[5],
                    "sexo": r[6]
                }
                for r in rows
            ]
        except psycopg2.DatabaseError as e:
            app.logger.error(f"Error al obtener personas: {e}")
            return []
        finally:
            cur.close()
            con.close()

    def getPersonaById(self, id_persona):
        sql = """
        SELECT id_persona, fun_id, nombres, apellidos, ci, fechanac, sexo
        FROM personas WHERE id_persona = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_persona,))
            r = cur.fetchone()
            if r:
                return {
                    "id_persona": r[0],
                    "fun_id": r[1],
                    "nombres": r[2],
                    "apellidos": r[3],
                    "ci": r[4],
                    "fechanac": r[5].strftime('%Y-%m-%d') if r[5] else None,
                    "sexo": r[6]
                }
            return None
        except psycopg2.DatabaseError as e:
            app.logger.error(f"Error al obtener persona por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    def guardarPersona(self, nombres, apellidos, ci, fechanac, sexo, fun_id=None):
        try:
            fecha_nac = self._parse_fecha(fechanac)
            sexo_val = self._validar_sexo(sexo)
        except ValueError as e:
            return False, str(e), 400

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            if fun_id is None:
                sql = """
                INSERT INTO public.personas(nombres, apellidos, ci, fechanac, sexo)
                VALUES (%s, %s, %s, %s, %s) RETURNING id_persona
                """
                cur.execute(sql, (nombres, apellidos, ci, fecha_nac, sexo_val))
            else:
                sql = """
                INSERT INTO public.personas(fun_id, nombres, apellidos, ci, fechanac, sexo)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_persona
                """
                cur.execute(sql, (fun_id, nombres, apellidos, ci, fecha_nac, sexo_val))

            nuevo_id = cur.fetchone()[0]
            con.commit()
            app.logger.info("Persona insertada correctamente.")
            return True, nuevo_id, 201
        except errors.UniqueViolation:
            con.rollback()
            return False, "Ya existe una persona registrada con ese número de cédula (CI).", 409
        except errors.StringDataRightTruncation:
            con.rollback()
            return False, "Uno de los textos excede la longitud máxima permitida.", 400
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al insertar persona: {e}")
            return False, "Error en la base de datos al guardar persona.", 500
        finally:
            cur.close()
            con.close()

    def updatePersona(self, id_persona, nombres, apellidos, ci, fechanac, sexo, fun_id=None):
        try:
            fecha_nac = self._parse_fecha(fechanac)
            sexo_val = self._validar_sexo(sexo)
        except ValueError as e:
            return False, str(e), 400

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            if fun_id is None:
                sql = """
                UPDATE personas
                SET nombres=%s, apellidos=%s, ci=%s, fechanac=%s, sexo=%s,
                    modificacion_fecha = CURRENT_DATE,
                    modificacion_hora = CURRENT_TIME
                WHERE id_persona=%s
                """
                cur.execute(sql, (nombres, apellidos, ci, fecha_nac, sexo_val, id_persona))
            else:
                sql = """
                UPDATE personas
                SET fun_id=%s, nombres=%s, apellidos=%s, ci=%s, fechanac=%s, sexo=%s,
                    modificacion_fecha = CURRENT_DATE,
                    modificacion_hora = CURRENT_TIME
                WHERE id_persona=%s
                """
                cur.execute(sql, (fun_id, nombres, apellidos, ci, fecha_nac, sexo_val, id_persona))

            if cur.rowcount == 0:
                con.rollback()
                return False, "Persona no encontrada.", 404

            con.commit()
            app.logger.info("Persona actualizada correctamente.")
            return True, "Persona actualizada correctamente.", 200
        except errors.UniqueViolation:
            con.rollback()
            return False, "El número de cédula (CI) ya pertenece a otra persona.", 409
        except errors.StringDataRightTruncation:
            con.rollback()
            return False, "Uno de los textos excede la longitud máxima permitida.", 400
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al actualizar persona: {e}")
            return False, "Error al actualizar persona.", 500
        finally:
            cur.close()
            con.close()

    def deletePersona(self, id_persona):
        sql = "DELETE FROM personas WHERE id_persona=%s"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_persona,))
            if cur.rowcount == 0:
                con.rollback()
                return False, "Persona no encontrada.", 404
            con.commit()
            app.logger.info("Persona eliminada correctamente.")
            return True, "Persona eliminada correctamente.", 200
        except errors.ForeignKeyViolation:
            con.rollback()
            return False, "No se puede eliminar la persona porque está asociada a clientes, proveedores o usuarios.", 400
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al eliminar persona: {e}")
            return False, "Error al eliminar persona.", 500
        finally:
            cur.close()
            con.close()
