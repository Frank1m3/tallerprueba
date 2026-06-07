from flask import current_app as app
from app.conexion.Conexion import Conexion


class VentaDao:

    # ================================
    # Buscar producto por código de barra o nombre
    # ================================
    def buscarProducto(self, termino):
        sql = """
        SELECT DISTINCT
            i.id_item,
            i.item_code,
            i.descripcion,
            i.precio_unitario,
            i.id_tipo_impuesto,
            t.descripcion AS tipo_impuesto,
            COALESCE(s.cantidad, 0) AS stock
        FROM item i
        LEFT JOIN tipo_impuesto t ON t.id_tipo_impuesto::text = i.id_tipo_impuesto
        LEFT JOIN stock s ON s.id_item = i.id_item
        LEFT JOIN barras b ON b.id_item = i.id_item
        WHERE (
            LOWER(i.descripcion) LIKE LOWER(%s)
            OR i.item_code = %s
            OR b.cod_barra = %s
        )
        ORDER BY i.descripcion
        LIMIT 15
        """
        like = f"%{termino}%"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (like, termino, termino))
            filas = cur.fetchall()
            return [{
                "id_item":          f[0],
                "item_code":        f[1],
                "descripcion":      f[2],
                "precio_unitario":  float(f[3]) if f[3] else 0.0,
                "id_tipo_impuesto": f[4],
                "tipo_impuesto":    f[5] or '',
                "stock":            float(f[6])
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al buscar producto: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Buscar cliente por RUC o cédula
    # ================================
    def buscarCliente(self, termino):
        sql = """
        SELECT id_clie, clie_nombre, clie_ci, clie_telefono, clie_direccion
        FROM cliente
        WHERE LOWER(clie_nombre) LIKE LOWER(%s)
           OR clie_ci LIKE %s
        ORDER BY clie_nombre
        LIMIT 10
        """
        like = f"%{termino}%"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql, (like, like))
            filas = cur.fetchall()
            return [{
                "id_cliente":      f[0],
                "nombre_completo": f[1] or '',
                "cedula":          f[2] or '',
                "telefono":        f[3] or '',
                "direccion":       f[4] or '',
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al buscar cliente: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener siguiente código de venta
    # ================================
    def getSiguienteCodigoVenta(self):
        sql = "SELECT COALESCE(MAX(id_venta_cab), 0) + 1 FROM venta_cab"
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            nro = cur.fetchone()[0]
            return f"VTA-{str(nro).zfill(8)}"
        except Exception as e:
            app.logger.error(f"Error al obtener código venta: {e}")
            return "VTA-00000001"
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener apertura activa para vincular a la venta
    # ================================
    def getAperturaActiva(self):
        sql = """
        SELECT id_apertura, nro_turno
        FROM aperturas
        WHERE estado = 'activo'
        ORDER BY registro DESC
        LIMIT 1
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            row = cur.fetchone()
            if row:
                return {"id_apertura": row[0], "nro_turno": row[1]}
            return None
        except Exception as e:
            app.logger.error(f"Error al obtener apertura activa en venta: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Registrar venta (cabecera + detalle + cobro)
    # Falla si no hay apertura activa
    # ================================
    def registrarVenta(self, datos):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("BEGIN")

            # Verificar apertura activa
            cur.execute("SELECT id_apertura FROM aperturas WHERE estado = 'activo' LIMIT 1")
            apertura = cur.fetchone()
            if not apertura:
                cur.execute("ROLLBACK")
                return {"error": "No hay un turno abierto. Debe realizar una apertura de caja antes de registrar ventas."}

            id_apertura = apertura[0]

            # 1. Insertar cabecera con id_apertura
            cur.execute("""
                INSERT INTO venta_cab
                    (fun_id, id_sucursal, id_caja, codigo_venta, id_cliente,
                     fecha_venta, total_venta, estado, id_apertura)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s, 'PAGADO', %s)
                RETURNING id_venta_cab
            """, (
                datos['fun_id'],
                datos['id_sucursal'],
                datos.get('id_caja', 1),
                datos['codigo_venta'],
                datos.get('id_cliente'),
                datos['total_venta'],
                id_apertura
            ))
            id_venta_cab = cur.fetchone()[0]

            # 2. Insertar detalle
            for det in datos['detalle']:
                cur.execute("""
                    INSERT INTO venta_det
                        (id_venta_cab, item_code, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (
                    id_venta_cab,
                    det['item_code'],
                    det['cantidad'],
                    det['precio_unitario']
                ))

                # 3. Descontar stock
                cur.execute("""
                    UPDATE stock
                    SET cantidad = cantidad - %s,
                        fecha_ultima_actualizacion = NOW()
                    WHERE id_item = %s
                """, (det['cantidad'], det['id_item']))

            # 4. Registrar cobro
            cur.execute("""
                INSERT INTO cobro_cab
                    (monto_cobrado, fecha_cobro, referencia)
                VALUES (%s, CURRENT_DATE, %s)
                RETURNING id_cobro_cab
            """, (datos['total_venta'], f"VENTA-{id_venta_cab}"))
            id_cobro_cab = cur.fetchone()[0]

            # 5. Detalle de cobro por forma de pago
            for pago in datos['pagos']:
                cur.execute("""
                    INSERT INTO cobro_det
                        (id_cobro_cab, id_forma_cobro, id_cliente, monto_cobrado)
                    VALUES (%s, %s, %s, %s)
                """, (
                    id_cobro_cab,
                    pago['id_forma_cobro'],
                    datos.get('id_cliente'),
                    pago['monto']
                ))

                if pago.get('es_tarjeta') and pago.get('nro_tarjeta'):
                    cur.execute("""
                        INSERT INTO cobro_tarjeta
                            (id_cobro_cab, numero_tarjeta, monto)
                        VALUES (%s, %s, %s)
                    """, (id_cobro_cab, pago['nro_tarjeta'], pago['monto']))

            cur.execute("COMMIT")
            return id_venta_cab

        except Exception as e:
            cur.execute("ROLLBACK")
            app.logger.error(f"Error al registrar venta: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener venta por ID (para factura)
    # ================================
    def getVentaById(self, id_venta_cab):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("""
                SELECT v.id_venta_cab, v.codigo_venta, v.fecha_venta,
                       v.total_venta, v.estado,
                       c.clie_nombre AS cliente_nombre,
                       c.clie_ci AS cliente_ruc,
                       c.clie_direccion AS cliente_dir,
                       f.nombres || ' ' || f.apellidos AS vendedor
                FROM venta_cab v
                LEFT JOIN cliente c ON c.id_clie = v.id_cliente
                LEFT JOIN funcionarios f ON f.fun_id = v.fun_id
                WHERE v.id_venta_cab = %s
            """, (id_venta_cab,))
            cab = cur.fetchone()
            if not cab:
                return None

            venta = {
                "id_venta_cab":   cab[0],
                "codigo_venta":   cab[1],
                "fecha_venta":    cab[2].strftime("%d/%m/%Y") if cab[2] else '',
                "total_venta":    float(cab[3]) if cab[3] else 0.0,
                "estado":         cab[4],
                "cliente_nombre": cab[5] or 'CONSUMIDOR FINAL',
                "cliente_ruc":    cab[6] or '0000000-0',
                "cliente_dir":    cab[7] or '-',
                "vendedor":       cab[8] or '',
                "detalle":        []
            }

            cur.execute("""
                SELECT d.item_code, i.descripcion, d.cantidad,
                       d.precio_unitario, i.id_tipo_impuesto,
                       t.descripcion AS tipo_impuesto
                FROM venta_det d
                LEFT JOIN item i ON i.item_code = d.item_code
                LEFT JOIN tipo_impuesto t ON t.id_tipo_impuesto::text = i.id_tipo_impuesto
                WHERE d.id_venta_cab = %s
            """, (id_venta_cab,))
            for f in cur.fetchall():
                cant  = float(f[2])
                precio = float(f[3])
                venta['detalle'].append({
                    "item_code":       f[0],
                    "descripcion":     f[1] or '',
                    "cantidad":        cant,
                    "precio_unitario": precio,
                    "subtotal":        cant * precio,
                    "tipo_impuesto":   f[5] or ''
                })

            return venta

        except Exception as e:
            app.logger.error(f"Error al obtener venta: {e}")
            return None
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener formas de pago
    # ================================
    def getFormasPago(self):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("SELECT id, descripcion FROM formas_pago ORDER BY id")
            return [{"id": f[0], "descripcion": f[1]} for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener formas de pago: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener últimas ventas
    # ================================
    def getVentas(self):
        sql = """
        SELECT v.id_venta_cab, v.codigo_venta, v.fecha_venta,
               v.total_venta, v.estado,
               COALESCE(c.clie_nombre, 'CONSUMIDOR FINAL') AS cliente,
               f.nombres || ' ' || f.apellidos AS vendedor
        FROM venta_cab v
        LEFT JOIN cliente c ON c.id_clie = v.id_cliente
        LEFT JOIN funcionarios f ON f.fun_id = v.fun_id
        ORDER BY v.id_venta_cab DESC
        LIMIT 100
        """
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute(sql)
            filas = cur.fetchall()
            return [{
                "id_venta_cab": f[0],
                "codigo_venta": f[1],
                "fecha_venta":  f[2].strftime("%d/%m/%Y") if f[2] else '',
                "total_venta":  float(f[3]) if f[3] else 0.0,
                "estado":       f[4],
                "cliente":      f[5],
                "vendedor":     f[6] or ''
            } for f in filas]
        except Exception as e:
            app.logger.error(f"Error al obtener ventas: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener entidades emisoras (bancos para tarjeta)
    # ================================
    def getEntidadesEmisoras(self):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("SELECT id_entidad_emisora, descrpcion FROM entidad_emisora ORDER BY descrpcion")
            return [{"id": f[0], "descripcion": f[1]} for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener entidades emisoras: {e}")
            return []
        finally:
            cur.close()
            con.close()

    # ================================
    # Obtener entidades adheridas (redes QR)
    # ================================
    def getEntidadesAdheridas(self):
        conexion = Conexion()
        con = conexion.getConexion()
        cur = con.cursor()
        try:
            cur.execute("SELECT id_entidad_adherida, descripcion FROM entidad_adherida ORDER BY descripcion")
            return [{"id": f[0], "descripcion": f[1]} for f in cur.fetchall()]
        except Exception as e:
            app.logger.error(f"Error al obtener entidades adheridas: {e}")
            return []
        finally:
            cur.close()
            con.close()