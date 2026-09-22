from flask import current_app as app
from app.conexion.Conexion import Conexion
import psycopg2


class PermisoDao:

    def grupos(self):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("SELECT gru_id, gru_des FROM grupos ORDER BY gru_id")
            return [{"gru_id": r[0], "gru_des": r[1]} for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def matriz(self, gru_id):
        """Todas las ventanas con los permisos del grupo (sin fila = todo en falso)."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT p.pag_id, p.pag_nombre, m.mod_des,
                       COALESCE(pe.leer, FALSE), COALESCE(pe.insertar, FALSE),
                       COALESCE(pe.editar, FALSE), COALESCE(pe.borrar, FALSE)
                FROM paginas p
                JOIN modulos m ON m.mod_id = p.mod_id
                LEFT JOIN permisos pe ON pe.pag_id = p.pag_id AND pe.gru_id = %s
                WHERE p.pag_estado IS TRUE
                ORDER BY m.mod_id, p.pag_nombre
            """, (gru_id,))
            return [{"pag_id": r[0], "ventana": r[1], "modulo": r[2],
                     "leer": r[3], "insertar": r[4], "editar": r[5], "borrar": r[6]} for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def matriz_usuario(self, usu_id, gru_id):
        """Todas las ventanas con lo que da el perfil del usuario y, si existe,
        la excepción individual de ESE usuario (None = sin excepción, usa el perfil)."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            cur.execute("""
                SELECT p.pag_id, p.pag_nombre, m.mod_des,
                       COALESCE(pe.leer, FALSE), COALESCE(pe.insertar, FALSE),
                       COALESCE(pe.editar, FALSE), COALESCE(pe.borrar, FALSE),
                       pu.leer, pu.insertar, pu.editar, pu.borrar
                FROM paginas p
                JOIN modulos m ON m.mod_id = p.mod_id
                LEFT JOIN permisos pe ON pe.pag_id = p.pag_id AND pe.gru_id = %s
                LEFT JOIN permisos_usuario pu ON pu.pag_id = p.pag_id AND pu.usu_id = %s
                WHERE p.pag_estado IS TRUE
                ORDER BY m.mod_id, p.pag_nombre
            """, (gru_id, usu_id))
            return [{"pag_id": r[0], "ventana": r[1], "modulo": r[2],
                     "perfil": {"leer": r[3], "insertar": r[4], "editar": r[5], "borrar": r[6]},
                     "excepcion": {"leer": r[7], "insertar": r[8], "editar": r[9], "borrar": r[10]}}
                    for r in cur.fetchall()]
        finally:
            cur.close(); con.close()

    def guardar_usuario(self, usu_id, filas):
        """filas: [{pag_id, leer, insertar, editar, borrar}] con cada acción en
        None/True/False. Sin ninguna excepción marcada, no se guarda fila (o se
        borra la que hubiera): estar "sin fila" es el estado normal."""
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            for f in filas:
                pag_id = int(f["pag_id"])
                valores = {k: (None if f.get(k) is None else bool(f.get(k))) for k in ("leer", "insertar", "editar", "borrar")}
                if all(v is None for v in valores.values()):
                    cur.execute("DELETE FROM permisos_usuario WHERE usu_id = %s AND pag_id = %s", (usu_id, pag_id))
                    continue
                cur.execute("""
                    INSERT INTO permisos_usuario (usu_id, pag_id, leer, insertar, editar, borrar)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (usu_id, pag_id) DO UPDATE
                        SET leer = EXCLUDED.leer, insertar = EXCLUDED.insertar,
                            editar = EXCLUDED.editar, borrar = EXCLUDED.borrar
                """, (usu_id, pag_id, valores["leer"], valores["insertar"], valores["editar"], valores["borrar"]))
            con.commit()
            return True
        except (psycopg2.Error, KeyError, ValueError) as e:
            con.rollback()
            app.logger.error(f"Error al guardar permisos individuales: {e}")
            return False
        finally:
            cur.close(); con.close()

    def guardar(self, gru_id, filas):
        con = Conexion().getConexion(); cur = con.cursor()
        try:
            for f in filas:
                leer = bool(f.get("leer"))
                # sin acceso a la ventana no tiene sentido agregar/modificar/eliminar
                ins, edi, bor = (bool(f.get(k)) and leer for k in ("insertar", "editar", "borrar"))
                cur.execute("""
                    INSERT INTO permisos (pag_id, gru_id, leer, insertar, editar, borrar)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pag_id, gru_id) DO UPDATE
                        SET leer = EXCLUDED.leer, insertar = EXCLUDED.insertar,
                            editar = EXCLUDED.editar, borrar = EXCLUDED.borrar
                """, (int(f["pag_id"]), gru_id, leer, ins, edi, bor))
            con.commit()
            return True
        except (psycopg2.Error, KeyError, ValueError) as e:
            con.rollback()
            app.logger.error(f"Error al guardar permisos: {e}")
            return False
        finally:
            cur.close(); con.close()
