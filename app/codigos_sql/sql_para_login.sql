SELECT 
	u.usu_id
	, TRIM(u.usu_nick) nick
	, u.usu_clave
	, u.usu_nro_intentos
    , u.fun_id
	, u.gru_id
	, u.usu_estado
    , CONCAT(p.per_nombres, ' ', p.per_apellidos)nombre_persona
	, g.gru_des grupo
FROM 
	usuarios u
left join 
	personas p on p.id_persona = u.fun_id
left join 
	grupos g ON g.gru_id = u.gru_id
WHERE 
	u.usu_nick = 'carlos' AND u.usu_estado is true