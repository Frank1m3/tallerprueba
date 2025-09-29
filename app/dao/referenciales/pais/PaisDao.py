from flask import current_app as app
from app.conexion.Conexion import Conexion

class PaisDao:

    def getPaises(self):

        paisSQL = """
        SELECT id, descripcion 
        FROM paises
        """

        # objeto conexion
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(paisSQL)
            lista_paises = cur.fetchall()
            return [ { "id": item[0], "descripcion": item[1] } for item in lista_paises]
        except con.Error as e:
             app.logger.info(e)
        finally:
            cur.close()
            con.close()

    def getPaisById(self, id):

        paisSQL = """
        SELECT id, descripcion
        FROM paises WHERE id=%s
        """
        # objeto conexion
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(paisSQL, (id,))
            # trae datos de la bd
            paisEncontrado = cur.fetchone()
            # retorno los datos
            return {
                    "id": paisEncontrado[0],
                    "descripcion": paisEncontrado[1]
                }
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()


    def guardarPais(self, descripcion):   
        insertPaisSQL = """
        INSERT INTO paises(descripcion) VALUES(%s)
        """

        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()        

        try:
            cur.execute(insertPaisSQL, (descripcion,))

            con.commit()   
            return True

        except con.Error as e:
            app.logger.info(e)

        finally:
            cur.close()
            con.close()
            return False        
        
    def updatePais(self, id, descripcion):

            updatePaisSQL = """
            UPDATE paises
            SET descripcion=%s
            WHERE id=%s
            """

            conexion = Conexion()
            con = conexion.getConexion()
            cur = con.cursor()

            # Ejecucion exitosa
            try:
                cur.execute(updatePaisSQL, (descripcion, id,))
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
    
    def deletePais(self, id):

            updatePaisSQL = """
            DELETE FROM paises
            WHERE id=%s
            """

            conexion = Conexion()
            con = conexion.getConexion()
            cur = con.cursor()

            # Ejecucion exitosa
            try:
                cur.execute(updatePaisSQL, (id,))
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