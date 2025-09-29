from flask import current_app as app
from app.conexion.Conexion import Conexion

class MarcaDao:

    def getMarcas(self):
        marcaSQL = """
        SELECT id, descripcion
        FROM marcas
        """
        # objeto conexion
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(marcaSQL)
            # trae datos de la bd
            lista_marcas = cur.fetchall()
            # retorno los datos
            lista_ordenada = []
            for item in lista_marcas:
                lista_ordenada.append({
                    "id": item[0],
                    "descripcion": item[1]
                })
            return lista_ordenada
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

    def getMarcaById(self, id):
        marcaSQL = """
        SELECT id, descripcion
        FROM marcas WHERE id=%s
        """
        # objeto conexion
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(marcaSQL, (id,))
            # trae datos de la bd
            marcaEncontrada = cur.fetchone()
            # retorno los datos
            return {
                "id": marcaEncontrada[0],
                "descripcion": marcaEncontrada[1]
            }
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

    def guardarMarca(self, descripcion):
        insertMarcaSQL = """
        INSERT INTO marcas(descripcion) VALUES(%s)
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecucion exitosa
        try:
            cur.execute(insertMarcaSQL, (descripcion,))
            # se confirma la insercion
            con.commit()
            return True

        # Si algo fallo entra aqui
        except con.Error as e:
            app.logger.info(e)

        # Siempre se va ejecutar
        finally:
            cur.close()
            con.close()

        return False

    def updateMarca(self, id, descripcion):
        updateMarcaSQL = """
        UPDATE marcas
        SET descripcion=%s
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecucion exitosa
        try:
            cur.execute(updateMarcaSQL, (descripcion, id,))
            # se confirma la insercion
            con.commit()
            return True

        # Si algo fallo entra aqui
        except con.Error as e:
            app.logger.info(e)

        # Siempre se va ejecutar
        finally:
            cur.close()
            con.close()

        return False

    def deleteMarca(self, id):
        deleteMarcaSQL = """
        DELETE FROM marcas
        WHERE id=%s
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        # Ejecucion exitosa
        try:
            cur.execute(deleteMarcaSQL, (id,))
            # se confirma la insercion
            con.commit()
            return True

        # Si algo fallo entra aqui
        except con.Error as e:
            app.logger.info(e)

        # Siempre se va ejecutar
        finally:
            cur.close()
            con.close()

        return False
