from flask import current_app as app
from app.conexion.Conexion import Conexion

class AperturaDao:
    def getAperturas(self):
        # Consulta SQL para obtener todas las aperturas
        aperturaSQL = """
        SELECT a.id_apertura, a.nro_turno, upper(p.nombres || ' ' || p.apellidos) as fiscal, 
               upper(p2.nombres || ' ' || p2.apellidos) as cajero, 
               to_char(a.registro, 'DD/MM/YYYY HH24:MI:SS') as registro, 
               a.monto_inicial, a.estado
        FROM aperturas a
        LEFT JOIN personas p ON a.clave_fiscal = p.fun_id
        LEFT JOIN personas p2 ON a.cajero = p2.fun_id
        """
        
        # Conexión a la base de datos
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        
        try:
            cur.execute(aperturaSQL)
            lista_aperturas = cur.fetchall()  # Trae los datos de la base de datos
            
            lista_ordenada = []
            ultimo_turno = None  # Variable para almacenar el último turno
            
            for item in lista_aperturas:
                lista_ordenada.append({
                    "id_apertura": item[0],
                    "nro_turno": item[1],
                    "clave_fiscal": item[2],
                    "cajero": item[3],
                    "registro": item[4],
                    "monto_inicial": item[5],
                    "estado": item[6]
                })
                
                # Determinar el último nro_turno
                if ultimo_turno is None or item[1] > ultimo_turno:
                    ultimo_turno = item[1]
                    
            return lista_ordenada, ultimo_turno  # Devuelve también el último nro_turno

        except con.Error as e:
            app.logger.error(f"Error al obtener aperturas: {e}")
            return [], None  # Devuelve None si no se encuentra el turno
        
        finally:
            cur.close()
            con.close()
   
    def getAperturaById(self, id_apertura):
        # Consulta SQL para obtener una apertura específica por su ID
        aperturaSQL = """
        SELECT id_apertura, nro_turno, clave_fiscal, cajero, registro, estado
        FROM aperturas WHERE id_apertura = %s
        """
        
        # Conexión a la base de datos
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(aperturaSQL, (id_apertura,))
            aperturaEncontrada = cur.fetchone()  # Trae los datos de la base de datos

            if aperturaEncontrada:
                return {
                    "id_apertura": aperturaEncontrada[0],
                    "nro_turno": aperturaEncontrada[1],
                    "clave_fiscal": aperturaEncontrada[2],
                    "cajero": aperturaEncontrada[3],
                    "registro": aperturaEncontrada[4],
                    "estado": aperturaEncontrada[5]
                }
            return None
        
        except con.Error as e:
            app.logger.error(f"Error al obtener apertura por ID: {e}")
            return None
        
        finally:
            cur.close()
            con.close()
            

    def guardarApertura(self, clave_fiscal, cajero, monto_inicial):
        # Consulta para insertar una nueva apertura
        insertAperturaSQL = """
        INSERT INTO aperturas (clave_fiscal, cajero, monto_inicial)
        SELECT %s, %s, %s
        WHERE EXISTS (
            SELECT 1
            FROM funcionarios f_clave_fiscal
            WHERE f_clave_fiscal.fun_id = %s
            AND f_clave_fiscal.es_fiscal = TRUE
        ) 
        AND EXISTS (
            SELECT 1
            FROM funcionarios f2_cajero
            WHERE f2_cajero.fun_id = %s
            AND f2_cajero.es_cajero = TRUE
        ) 
        AND %s != %s
        AND NOT EXISTS (
            SELECT 1
            FROM funcionarios f_check
            WHERE f_check.fun_id = %s
            AND f_check.es_fiscal = TRUE
            AND f_check.es_cajero = TRUE
        )
        RETURNING id_apertura;
        """
        
        # Conexión a la base de datos
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(insertAperturaSQL, (clave_fiscal, cajero, monto_inicial, clave_fiscal, cajero, clave_fiscal, cajero, clave_fiscal))
            result = cur.fetchone()  # Obtener el id_apertura generado por la base de datos

            if result:
                id_apertura = result[0]
                con.commit()  # Confirmar la transacción
                return {"id_apertura": id_apertura}
            else:
                return None  # Si no se pudo insertar la apertura, devolver None

        except Exception as e:
            app.logger.error(f"Error al insertar apertura: {e}")
            con.rollback()  # Deshacer la transacción en caso de error
            return None
        
        finally:
            cur.close()
            con.close()

    def anularApertura(self, id_apertura):
        # Consulta SQL para anular una apertura
        updateAperturaSQL = """
        UPDATE aperturas
        SET estado = 'anulado'
        WHERE id_apertura = %s AND estado = 'activo'
        """
        
        # Conexión a la base de datos
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()

        try:
            cur.execute(updateAperturaSQL, (id_apertura,))
            con.commit()
            if cur.rowcount > 0:
                return True  # Apertura anulada con éxito
            return False  # No se encontró la apertura o no se actualizó

        except con.Error as e:
            app.logger.error(f"Error al anular apertura: {e}")
            return False
        
        finally:
            cur.close()
            con.close()
