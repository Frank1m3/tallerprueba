```python

from datetime import date

# Ejemplo de conversión en tu DAO
fecha_str = '2024-10-16'  # Suponiendo que recibes la fecha como cadena
fecha_pedido = date.fromisoformat(fecha_str)  # Conversión de string a date


```

```python

from datetime import date
fecha_pedido=date(2024, 10, 16)


```

### Paquetes a instalar
`pip install flask-wtf`



from werkzeug.security import generate_password_hash

# Contraseña del usuario
password = '12345' 

# Generar el hash de la contraseña
password_hash = generate_password_hash(password)

# El hash generado sería algo como:
# pbkdf2:sha256:260000$bxZuwErVt5fRAnFq$9b44b79537b6f497e4f58f105eb1693cd9d81d8b951a87d13b50abed8ac320c7
print(password_hash)


