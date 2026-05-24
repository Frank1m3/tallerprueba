from flask import current_app as app
from app.conexion.Conexion import Conexion


class AperturaDao:

    # ================================
    # Obtener todas las aperturas
    # ================================
    def getAperturas(self):
        aperturaSQL = """
        SELECT a.id_apertura, a.nro_turno,
               UPPER(f1.nombres || ' ' || f1.apellidos) AS fiscal,
               UPPER(f2.nombres || ' ' || f2.apellidos) AS cajero,
               to_char(a.registro, 'DD/MM/YYYY HH24:MI:SS') AS registro,
               a.monto_inicial, a.estado
        FROM aperturas a
        LEFT JOIN funcionarios f1 ON f1.fun_id = a.clave_fiscal
        LEFT JOIN funcionarios f2 ON f2.fun_id = a.cajero
        ORDER BY a.nro_turno DESC
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(aperturaSQL)
            filas = cur.fetchall()
            lista = []
            ultimo_turno = None
            for item in filas:
                lista.append({
                    "id_apertura":  item[0],
                    "nro_turno":    item[1],
                    "clave_fiscal": item[2] or '',
                    "cajero":       item[3] or '',
                    "registro":     item[4],
                    "monto_inicial":item[5],
                    "estado":       item[6]
                })
                if ultimo_turno is None or item[1] > ultimo_turno:
                    ultimo_turno = item[1]
            return lista, ultimo_turno
        except Exception as e:
            app.logger.error(f"Error al obtener aperturas: {e}")
            return [], None
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener apertura por ID
    # ================================
    def getAperturaById(self, id_apertura):
        aperturaSQL = """
        SELECT a.id_apertura, a.nro_turno, a.clave_fiscal, a.cajero,
               to_char(a.registro, 'DD/MM/YYYY HH24:MI:SS') AS registro,
               a.monto_inicial, a.estado
        FROM aperturas a
        WHERE a.id_apertura = %s
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(aperturaSQL, (id_apertura,))
            row = cur.fetchone()
            if row:
                return {
                    "id_apertura":  row[0],
                    "nro_turno":    row[1],
                    "clave_fiscal": row[2],
                    "cajero":       row[3],
                    "registro":     row[4],
                    "monto_inicial":row[5],
                    "estado":       row[6]
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener apertura por ID: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # NUEVO: Validar fiscal por su fun_id (clave)
    # Retorna sus datos si es fiscal activo, None si no existe o no es fiscal
    # ================================
    def getFiscalByClave(self, fun_id):
        sql = """
        SELECT fun_id, nombres, apellidos, ci
        FROM funcionarios
        WHERE fun_id = %s
          AND es_fiscal = TRUE
          AND fun_estado = TRUE
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (fun_id,))
            row = cur.fetchone()
            if row:
                return {
                    "fun_id":    row[0],
                    "nombres":   row[1],
                    "apellidos": row[2],
                    "ci":        row[3],
                    "nombre_completo": f"{row[1]} {row[2]}"
                }
            return None
        except Exception as e:
            app.logger.error(f"Error al validar fiscal: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # NUEVO: Buscar cajeros por nombre/apellido (para el buscador)
    # ================================
    def buscarCajeros(self, termino):
        sql = """
        SELECT fun_id, nombres, apellidos, ci
        FROM funcionarios
        WHERE es_cajero = TRUE
          AND fun_estado = TRUE
          AND (
              LOWER(nombres)   LIKE LOWER(%s)
           OR LOWER(apellidos) LIKE LOWER(%s)
           OR LOWER(nombres || ' ' || apellidos) LIKE LOWER(%s)
           OR ci LIKE %s
          )
        ORDER BY nombres, apellidos
        LIMIT 10
        """
        like = f"%{termino}%"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (like, like, like, like))
            filas = cur.fetchall()
            return [{
                "fun_id":          row[0],
                "nombres":         row[1],
                "apellidos":       row[2],
                "ci":              row[3],
                "nombre_completo": f"{row[1]} {row[2]}"
            } for row in filas]
        except Exception as e:
            app.logger.error(f"Error al buscar cajeros: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Guardar apertura
    # ================================
    def guardarApertura(self, clave_fiscal, cajero, monto_inicial):
        insertAperturaSQL = """
        INSERT INTO aperturas (clave_fiscal, cajero, monto_inicial)
        SELECT %s, %s, %s
        WHERE EXISTS (
            SELECT 1 FROM funcionarios
            WHERE fun_id = %s AND es_fiscal = TRUE AND fun_estado = TRUE
        )
        AND EXISTS (
            SELECT 1 FROM funcionarios
            WHERE fun_id = %s AND es_cajero = TRUE AND fun_estado = TRUE
        )
        AND %s != %s
        RETURNING id_apertura
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(insertAperturaSQL, (
                clave_fiscal, cajero, monto_inicial,
                clave_fiscal, cajero,
                clave_fiscal, cajero
            ))
            result = cur.fetchone()
            if result:
                con.commit()
                return {"id_apertura": result[0]}
            return None
        except Exception as e:
            app.logger.error(f"Error al insertar apertura: {e}")
            con.rollback()
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Anular apertura
    # ================================
    def anularApertura(self, id_apertura):
        sql = """
        UPDATE aperturas
        SET estado = 'anulado'
        WHERE id_apertura = %s AND estado = 'activo'
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (id_apertura,))
            con.commit()
            return cur.rowcount > 0
        except Exception as e:
            app.logger.error(f"Error al anular apertura: {e}")
            con.rollback()
            return False
        finally:
            cur.close()
            con.close()