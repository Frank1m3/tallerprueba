import re
from datetime import datetime, date
from flask import jsonify

def error_response(mensaje, status_code=400):
    """Retorna una respuesta JSON estandarizada de error."""
    return jsonify({
        'success': False,
        'error': mensaje
    }), status_code

def success_response(data=None, mensaje=None, status_code=200):
    """Retorna una respuesta JSON estandarizada de éxito."""
    resp = {'success': True, 'error': None}
    if data is not None:
        resp['data'] = data
    if mensaje is not None:
        resp['mensaje'] = mensaje
    return jsonify(resp), status_code

def validar_texto(valor, campo_nombre="campo", min_len=1, max_len=70, solo_letras=False, permitir_numeros=True):
    """
    Valida un campo de texto:
    - Verifica que sea una cadena de texto (str).
    - Aplica trim para eliminar espacios iniciales y finales.
    - Comprueba longitudes mínima y máxima.
    - Opcionalmente restringe el contenido a solo letras y espacios.
    """
    if valor is None:
        return False, f"El campo {campo_nombre} es obligatorio.", ""
    
    if not isinstance(valor, str):
        return False, f"El campo {campo_nombre} debe ser una cadena de texto.", ""
    
    valor_limpio = valor.strip()
    
    if len(valor_limpio) < min_len:
        return False, f"El campo {campo_nombre} es obligatorio y no puede estar vacío.", ""
    
    if max_len is not None and len(valor_limpio) > max_len:
        return False, f"El campo {campo_nombre} no puede exceder los {max_len} caracteres.", ""
    
    if solo_letras:
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\,\']+$"
        if not re.match(patron, valor_limpio):
            return False, f"El campo {campo_nombre} solo puede contener letras y espacios.", ""
    elif not permitir_numeros:
        if valor_limpio.isdigit():
            return False, f"El campo {campo_nombre} no puede ser únicamente numérico.", ""
            
    return True, "", valor_limpio

def validar_ci(valor, campo_nombre="Cédula de Identidad"):
    """Valida que la cédula sea válida (números positivos sin letras ni signos negativos)."""
    if valor is None:
        return False, f"El campo {campo_nombre} es obligatorio.", ""
    
    valor_str = str(valor).strip()
    if len(valor_str) == 0:
        return False, f"El campo {campo_nombre} es obligatorio.", ""
    
    if valor_str.startswith('-'):
        return False, f"El campo {campo_nombre} no puede ser un número negativo.", ""
    
    # Permitir puntos como separadores de miles
    valor_limpio = valor_str.replace(".", "").replace(" ", "").strip()
    
    if not valor_limpio.isdigit():
        return False, f"El campo {campo_nombre} debe contener solo dígitos numéricos válidos.", ""
    
    num = int(valor_limpio)
    if num <= 0:
        return False, f"El campo {campo_nombre} debe ser un número positivo mayor a 0.", ""
    
    if len(valor_str) > 20:
        return False, f"El campo {campo_nombre} no puede exceder los 20 caracteres.", ""
        
    return True, "", valor_str

def validar_fecha(valor, campo_nombre="Fecha", permitir_futuro=False, formatos=None):
    """
    Valida que la fecha tenga formato válido (YYYY-MM-DD o DD/MM/YYYY)
    y sea una fecha real en el calendario.
    """
    if valor is None:
        return False, f"El campo {campo_nombre} es obligatorio.", None
    
    if not isinstance(valor, str):
        return False, f"El campo {campo_nombre} debe ser una cadena de fecha.", None
    
    valor_limpio = valor.strip()
    if len(valor_limpio) == 0:
        return False, f"El campo {campo_nombre} es obligatorio.", None
    
    if formatos is None:
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
    
    fecha_valida = None
    for fmt in formatos:
        try:
            fecha_valida = datetime.strptime(valor_limpio, fmt).date()
            break
        except ValueError:
            continue
            
    if fecha_valida is None:
        return False, f"El campo {campo_nombre} tiene un formato de fecha inválido o no existe en el calendario (ej: AAAA-MM-DD).", None
    
    if not permitir_futuro and fecha_valida > date.today():
        return False, f"El campo {campo_nombre} no puede ser una fecha futura.", None
        
    return True, "", fecha_valida.strftime('%Y-%m-%d')

def validar_entero(valor, campo_nombre="campo", min_val=1, max_val=None):
    """Valida que el valor sea un entero positivo/válido."""
    if valor is None or valor == "":
        return False, f"El campo {campo_nombre} es obligatorio.", None
    
    try:
        val_int = int(valor)
    except (ValueError, TypeError):
        return False, f"El campo {campo_nombre} debe ser un número entero válido.", None
        
    if min_val is not None and val_int < min_val:
        return False, f"El campo {campo_nombre} debe ser mayor o igual a {min_val}.", None
        
    if max_val is not None and val_int > max_val:
        return False, f"El campo {campo_nombre} debe ser menor o igual a {max_val}.", None
        
    return True, "", val_int

def validar_decimal(valor, campo_nombre="campo", min_val=0, max_val=None):
    """Valida que el valor sea un número decimal/monetario válido."""
    if valor is None or valor == "":
        return False, f"El campo {campo_nombre} es obligatorio.", None
    
    try:
        val_float = float(valor)
    except (ValueError, TypeError):
        return False, f"El campo {campo_nombre} debe ser un valor numérico válido.", None
        
    if min_val is not None and val_float < min_val:
        return False, f"El campo {campo_nombre} no puede ser negativo (mínimo: {min_val}).", None
        
    if max_val is not None and val_float > max_val:
        return False, f"El campo {campo_nombre} no puede superar {max_val}.", None
        
    return True, "", val_float

def validar_sexo(valor, campo_nombre="Sexo"):
    """Valida opciones de sexo."""
    if valor is None:
        return False, f"El campo {campo_nombre} es obligatorio.", ""
    
    if not isinstance(valor, str):
        return False, f"El campo {campo_nombre} debe ser texto.", ""
        
    val = valor.strip().upper()
    validos = {'M': 'MASCULINO', 'F': 'FEMENINO', 'MASCULINO': 'MASCULINO', 'FEMENINO': 'FEMENINO', 'OTRO': 'OTRO'}
    
    if val not in validos:
        return False, f"El campo {campo_nombre} debe ser 'M', 'F' u 'OTRO'.", ""
        
    return True, "", val[0] if len(val) == 1 else val
