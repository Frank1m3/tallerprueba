from flask import current_app as app
from app.conexion.Conexion import Conexion

class SexoDao:

    # Obtener todos los sexos
    def getSexos(self):
        sexoSQL = """
        SELECT id, descripcion
        FROM sexo
        """
        # Objeto conexión
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sexoSQL)
            # Trae datos de la BD
            lista_sexos = cur.fetchall()
            # Retorno los datos
            lista_ordenada = []
            for item in lista_sexos:
                lista_ordenada.append({
                    "id": item[0],
                    "descripcion": item[1]
                })
            return lista_ordenada
        except con.Error as e:
            app.logger.error(f"Error al obtener todos los sexos: {str(e)}")
        finally:
            cur.close()
            con.close()

    # Obtener sexo por ID
    def getSexoById(self, id):
        sexoSQL = """
        SELECT id, descripcion
        FROM sexo WHERE id=%s
        """
        # Objeto conexión
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sexoSQL, (id,))
            # Trae datos de la BD
            sexoEncontrado = cur.fetchone()
            # Retorno los datos
            if sexoEncontrado:
                return {
                    "id": sexoEncontrado[0],
                    "descripcion": sexoEncontrado[1]
                }
            return None
        except con.Error as e:
            app.logger.error(f"Error al obtener sexo por ID: {str(e)}")
        finally:
            cur.close()
            con.close()

    # Guardar un nuevo sexo
    def guardarSexo(self, descripcion):
        insertSexoSQL = """
        INSERT INTO sexo(descripcion) VALUES(%s) RETURNING id
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(insertSexoSQL, (descripcion,))
            # Se confirma la inserción
            con.commit()
            sexo_id = cur.fetchone()[0]  # Obtiene el ID del nuevo registro
            return sexo_id
        except con.Error as e:
            app.logger.error(f"Error al guardar sexo: {str(e)}")
        finally:
            cur.close()
            con.close()

        return None

    # Actualizar un sexo
    def updateSexo(self, id, descripcion):
        updateSexoSQL = """
        UPDATE sexo
        SET descripcion=%s
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(updateSexoSQL, (descripcion, id,))
            # Se confirma la actualización
            con.commit()
            return cur.rowcount > 0  # Devuelve True si se actualizó al menos una fila
        except con.Error as e:
            app.logger.error(f"Error al actualizar sexo: {str(e)}")
        finally:
            cur.close()
            con.close()

        return False

    # Eliminar un sexo
    def deleteSexo(self, id):
        deleteSexoSQL = """
        DELETE FROM sexo
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecución exitosa
        try:
            cur.execute(deleteSexoSQL, (id,))
            # Se confirma la eliminación
            con.commit()
            return cur.rowcount > 0  # Devuelve True si se eliminó al menos una fila
        except con.Error as e:
            app.logger.error(f"Error al eliminar sexo: {str(e)}")
        finally:
            cur.close()
            con.close()

        return False
