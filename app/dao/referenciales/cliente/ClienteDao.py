from flask import current_app as app
from app.conexion.Conexion import Conexion

class ClienteDao:

    def getClientes(self):
        clienteSQL = """
        SELECT id_cliente, id_persona, nombre, apellido, cedula, direccion, telefono, fecha_registro
        FROM clientes
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(clienteSQL)
            lista_clientes = cur.fetchall()
            lista_ordenada = []
            for item in lista_clientes:
                lista_ordenada.append({
                    "id_cliente": item[0],
                    "id_persona": item[1],  # Relación opcional
                    "nombre": item[2],
                    "apellido": item[3],
                    "cedula": item[4],
                    "direccion": item[5],
                    "telefono": item[6],
                    "fecha_registro": item[7].strftime("%Y-%m-%d %H:%M:%S") if item[7] else None
                })
            return lista_ordenada
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

    def getClienteById(self, id_cliente):
        clienteSQL = """
        SELECT id_cliente, id_persona, nombre, apellido, cedula, direccion, telefono, fecha_registro
        FROM clientes WHERE id_cliente=%s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(clienteSQL, (id_cliente,))
            clienteEncontrado = cur.fetchone()
            if clienteEncontrado:
                return {
                    "id_cliente": clienteEncontrado[0],
                    "id_persona": clienteEncontrado[1],  # Relación opcional
                    "nombre": clienteEncontrado[2],
                    "apellido": clienteEncontrado[3],
                    "cedula": clienteEncontrado[4],
                    "direccion": clienteEncontrado[5],
                    "telefono": clienteEncontrado[6],
                    "fecha_registro": clienteEncontrado[7].strftime("%Y-%m-%d %H:%M:%S") if clienteEncontrado[7] else None
                }
            return None
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

    def guardarCliente(self, nombre, apellido, cedula, direccion, telefono):
        insertClienteSQL = """
        INSERT INTO clientes(nombre, apellido, cedula, direccion, telefono)
        VALUES (%s, %s, %s, %s, %s)
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(insertClienteSQL, (nombre, apellido, cedula, direccion, telefono))
            con.commit()
            return True, None
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

        return False, 'Error al guardar el cliente.'

    def updateCliente(self, id_cliente, nombre, apellido, cedula, direccion, telefono):
        updateClienteSQL = """
        UPDATE clientes
        SET nombre=%s, apellido=%s, cedula=%s, direccion=%s, telefono=%s
        WHERE id_cliente=%s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(updateClienteSQL, (nombre, apellido, cedula, direccion, telefono, id_cliente))
            con.commit()
            return True, None
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

        return False, 'Error al actualizar el cliente.'

    def deleteCliente(self, id_cliente):
        deleteClienteSQL = """
        DELETE FROM clientes
        WHERE id_cliente=%s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(deleteClienteSQL, (id_cliente,))
            con.commit()
            return True, None
        except con.Error as e:
            app.logger.info(e)
        finally:
            cur.close()
            con.close()

        return False, 'Error al eliminar el cliente.'
