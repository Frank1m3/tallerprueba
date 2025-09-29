from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2
from datetime import datetime

class PersonaDao:

    def _parse_fecha(self, fecha_str):
        """Convierte una fecha string a objeto date. Acepta dd/mm/yyyy o yyyy-mm-dd."""
        if not fecha_str:
            return None
        formatos = ['%d/%m/%Y', '%Y-%m-%d']
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha inválido: {fecha_str}")

    def _validar_sexo(self, sexo):
        """Valida y normaliza el sexo ('M' o 'F')."""
        if not sexo:
            return None
        sexo = sexo.strip().upper()
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
                    "fechanac": r[5],  # string en formato YYYY-MM-DD
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
        if not (nombres and apellidos and ci and sexo):
            app.logger.error("Faltan datos requeridos para insertar persona.")
            return False

        try:
            fecha_nac = self._parse_fecha(fechanac)
            sexo_val = self._validar_sexo(sexo)
        except ValueError as e:
            app.logger.error(f"Error en validación de datos: {e}")
            return False

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            if fun_id is None:
                sql = """
                INSERT INTO public.personas(nombres, apellidos, ci, fechanac, sexo)
                VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(sql, (nombres, apellidos, ci, fecha_nac, sexo_val))
            else:
                sql = """
                INSERT INTO public.personas(fun_id, nombres, apellidos, ci, fechanac, sexo)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (fun_id, nombres, apellidos, ci, fecha_nac, sexo_val))

            con.commit()
            app.logger.info("Persona insertada correctamente.")
            return True
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al insertar persona: {e}")
            return False
        finally:
            cur.close()
            con.close()

    def updatePersona(self, id_persona, nombres, apellidos, ci, fechanac, sexo, fun_id=None):
        if not (id_persona and nombres and apellidos and ci and sexo):
            app.logger.error("Faltan datos requeridos para actualizar persona.")
            return False

        try:
            fecha_nac = self._parse_fecha(fechanac)
            sexo_val = self._validar_sexo(sexo)
        except ValueError as e:
            app.logger.error(f"Error en validación de datos: {e}")
            return False

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

            con.commit()
            app.logger.info("Persona actualizada correctamente.")
            return True
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al actualizar persona: {e}")
            return False
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
            con.commit()
            app.logger.info("Persona eliminada correctamente.")
            return True
        except psycopg2.DatabaseError as e:
            con.rollback()
            app.logger.error(f"Error al eliminar persona: {e}")
            return False
        finally:
            cur.close()
            con.close()
