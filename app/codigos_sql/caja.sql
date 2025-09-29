CREATE TABLE sangria_caja (
	cod_empresa int4 NOT NULL,
	cod_local int4 NOT NULL,
	cod_caja int4 NOT NULL,
	nro_turno int4 NOT NULL,
	fec_alerta timestamp NOT NULL,
	can_alertas int4 NOT NULL,
	fec_sangria timestamp NOT NULL,
	nro_sangria int4 NOT NULL,
	vlr_caja numeric(15, 2) NOT NULL,
	vlr_sangria numeric(15, 2) NOT NULL,
	cod_cajero int4 NOT NULL,
	cod_fiscal int4 NOT NULL,
	estado varchar(1) NOT NULL,
	fec_vigencia timestamp NOT NULL,
	cod_usuario int4 NOT NULL,
	replicado varchar(1) NOT NULL,
	CONSTRAINT pk_sangria_caja PRIMARY KEY (cod_empresa, cod_local, cod_caja, nro_turno, nro_sangria)
);


CREATE TABLE articulolocal (
	cod_articulo int8 NOT NULL,
	cod_marca int4 NULL,
	cod_grupo int4 NULL,
	cod_subgrupo int4 NULL,
	cod_proveedor int4 NULL,
	descripcion varchar(55) NOT NULL,
	des_corta varchar(20) NOT NULL,
	pct_iva numeric(6, 2) NOT NULL,
	es_compuesto varchar(1) NOT NULL,
	es_pesable varchar(1) NOT NULL,
	hab_compra varchar(1) NULL,
	hab_venta varchar(1) NOT NULL,
	cod_envase int4 NULL,
	can_cupones int4 NULL,
	fec_catastro timestamp NULL,
	cod_usuario int4 NULL,
	fec_vigencia timestamp NULL,
	CONSTRAINT pk_articulocod_articulo PRIMARY KEY (cod_articulo)
);
CREATE INDEX articulo_descripcion ON articulolocal USING btree (descripcion);

-- Permissions

ALTER TABLE articulolocal OWNER TO postgres;
GRANT ALL ON TABLE articulolocal TO postgres;



CREATE TABLE cajalocal (
	cod_caja int4 NOT NULL,
	denominacion varchar(35) NOT NULL,
	secuencia_ticket int8 NOT NULL,
	secuencia_turno int8 NOT NULL,
	secuencia_zeta int8 NOT NULL,
	folio_inicial int8 NOT NULL,
	folio_final int8 NOT NULL,
	ult_act_local timestamp NOT NULL,
	ult_act_servidor timestamp NULL,
	actualiza_servidor varchar(1) NULL,
	replicado varchar(1) NULL,
	cod_sector int4 DEFAULT 0 NOT NULL,
	hace_trasferencia varchar(1) NULL,
	nro_timbrado varchar(13) NULL,
	validez_timbrado varchar(25) NULL,
	nro_timbrado_ncc varchar(13) NULL,
	validez_timbrado_ncc varchar(25) NULL,
	nro_remision_inicial int8 DEFAULT 0 NOT NULL,
	nro_remision_final int8 DEFAULT 0 NOT NULL,
	nro_notadebito_inicial numeric(7) DEFAULT 0 NOT NULL,
	nro_notadebito_final numeric(7) DEFAULT 0 NOT NULL,
	nro_timbrado_rpi varchar(13) DEFAULT '0'::character varying NOT NULL,
	validez_timbrado_rpi varchar(25) DEFAULT 'x'::character varying NOT NULL,
	nro_timbrado_fpi varchar(13) DEFAULT '0'::character varying NOT NULL,
	validez_timbrado_fpi varchar(25) DEFAULT '0'::character varying NOT NULL,
	validez_timbrado_inicio varchar(25) NULL,
	ip_pos_bancard varchar(15) NULL,
	es_caja_credito varchar(1) DEFAULT 'N'::character varying NOT NULL,
	salida_impresion varchar(10) DEFAULT 'LPT1'::character varying NOT NULL,
	emite_factura_electronica varchar(1) DEFAULT 'N'::character varying NOT NULL,
	serie_fv varchar(5) NULL,
	serie_nc varchar(5) NULL
);


CREATE TABLE forma_pagotmp (
	fec_cobro timestamp NOT NULL,
	nro_secuencia int4 NOT NULL,
	cod_cuenta int4 NOT NULL,
	denominacion_cta varchar(35) NOT NULL,
	tipo_cuenta varchar(3) NOT NULL,
	cod_moneda int4 NOT NULL,
	tip_cambio int8 NOT NULL,
	monto_pago numeric(12, 2) NOT NULL,
	monto_pago_gs numeric(12, 2) NOT NULL,
	nro_documento varchar(20) NOT NULL,
	nro_autorizacion varchar(15) NOT NULL,
	fec_emision date NOT NULL,
	fec_vencimiento date NOT NULL,
	nom_librador varchar(30) NOT NULL,
	cod_banco int4 NOT NULL,
	monto_dcto_fpago numeric(7, 2) NULL,
	pct_dcto_fpago numeric(7, 2) NULL
);


CREATE TABLE turnolocal (
	
	
	cod_caja int4 NOT NULL,
	nro_turno int8 NOT NULL,
	nro_zeta int8 NOT NULL,
	fec_hab_turno timestamp NOT NULL,
	fec_cierre_turno timestamp NULL,
	fec_cierre_caja timestamp NULL,
	cod_fis_habil int4 NOT NULL,
	cod_fis_cierrex int4 NULL,
	cod_fis_cierrez int4 NULL,
	cod_cajero int4 NOT NULL,
	sal_inicial numeric(10, 2) NOT NULL,
	ticket_inicial int8 NOT NULL,
	ticket_final int8 NOT NULL,
	fec_vigencia timestamp NOT NULL,
	cod_sector int4 DEFAULT 0 NOT NULL,
	CONSTRAINT pk_turno PRIMARY KEY (cod_empresa, cod_local, cod_caja, nro_turno)
);


CREATE TABLE aperturas (
	id_apertura SERIAL PRIMARY KEY,
	nro_turno SERIAL,
	fiscal INT,
	cajero INT,
	registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	monto_inicial decimal (15,2) NOT NULL,
	  FOREIGN KEY (cajero) REFERENCES funcionarios(id_personas),  -- Relación con la tabla de funcionarios
    FOREIGN KEY (fiscal) REFERENCES funcionarios(id_personas) 
);



-- Verificamos que tanto fiscal como cajero sean roles válidos y que no sean la misma persona
INSERT INTO aperturas (clave_fiscal, cajero, monto_inicial)
SELECT %s, %s, %s
WHERE EXISTS (
    -- Verificamos que el clave_fiscal corresponde a un fiscal
    SELECT 1
    FROM funcionarios f_clave_fiscal
    WHERE f_clave_fiscal.fun_id = %s
    AND f_clave_fiscal.es_fiscal = TRUE
) AND EXISTS (
    -- Verificamos que el cajero corresponde a un cajero
    SELECT 1
    FROM funcionarios f2_cajero
    WHERE f2_cajero.fun_id = %s
    AND f2_cajero.es_cajero = TRUE
) AND %s != %s;  -- Verificamos que el fiscal no sea el mismo que el cajero

 SELECT a.id_apertura, a.nro_turno, upper(p.nombres||' '||p.apellidos) as fiscal, upper(p2.nombres||' '||p2.apellidos) as cajero, to_char(a.registro,'DD/MM/YYYY HH24:MM:SS') as registro, a.monto_inicial
        FROM aperturas a 
       	left join funcionarios f on a.clave_fiscal = p.fun_id
       	left join personas p2 on a.cajero  = p2.fun_id 
        """

		select max(nro_turno)+1 nro_turno from aperturas a 