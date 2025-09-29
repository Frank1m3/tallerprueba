from flask import current_app as app
from app.conexion.Conexion import Conexion

class EstadoCivilDao:

    # Obtener todos los estados civiles
    def getEstadosCiviles(self):
        estadoCivilSQL = """
        SELECT id, descripcion
        FROM estado_civil
        """
        # Objeto conexión
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(estadoCivilSQL)
            # Trae datos de la BD
            lista_estados_civiles = cur.fetchall()
            # Retorno los datos
            lista_ordenada = []
            for item in lista_estados_civiles:
                lista_ordenada.append({
                    "id": item[0],
                    "descripcion": item[1]
                })
            return lista_ordenada
        except con.Error as e:
            app.logger.error(f"Error al obtener todos los estados civiles: {str(e)}")
        finally:
            cur.close()
            con.close()

    # Obtener estado civil por ID
    def getEstadoCivilById(self, id):
        estadoCivilSQL = """
        SELECT id, descripcion
        FROM estado_civil WHERE id=%s
        """
        # Objeto conexión
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(estadoCivilSQL, (id,))
            # Trae datos de la BD
            estadoCivilEncontrado = cur.fetchone()
            # Retorno los datos
            if estadoCivilEncontrado:
                return {
                    "id": estadoCivilEncontrado[0],
                    "descripcion": estadoCivilEncontrado[1]
                }
            return None
        except con.Error as e:
            app.logger.error(f"Error al obtener estado civil por ID: {str(e)}")
        finally:
            cur.close()
            con.close()

    # Guardar un nuevo estado civil
    def guardarEstadoCivil(self, descripcion):
        insertEstadoCivilSQL = """
        INSERT INTO estado_civil(descripcion) VALUES(%s) RETURNING id
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(insertEstadoCivilSQL, (descripcion,))
            # Se confirma la inserción
            con.commit()
            estado_civil_id = cur.fetchone()[0]  # Obtiene el ID del nuevo registro
            return estado_civil_id
        except con.Error as e:
            app.logger.error(f"Error al guardar estado civil: {str(e)}")
        finally:
            cur.close()
            con.close()

        return None

    # Actualizar un estado civil
    def updateEstadoCivil(self, id, descripcion):
        updateEstadoCivilSQL = """
        UPDATE estado_civil
        SET descripcion=%s
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(updateEstadoCivilSQL, (descripcion, id,))
            # Se confirma la actualización
            con.commit()
            return cur.rowcount > 0  # Devuelve True si se actualizó al menos una fila
        except con.Error as e:
            app.logger.error(f"Error al actualizar estado civil: {str(e)}")
        finally:
            cur.close()
            con.close()

        return False

    # Eliminar un estado civil
    def deleteEstadoCivil(self, id):
        deleteEstadoCivilSQL = """
        DELETE FROM estado_civil
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(deleteEstadoCivilSQL, (id,))
            # Se confirma la eliminación
            con.commit()
            return cur.rowcount > 0  # Devuelve True si se eliminó al menos una fila
        except con.Error as e:
            app.logger.error(f"Error al eliminar estado civil: {str(e)}")
        finally:
            cur.close()
            con.close()

        return False
