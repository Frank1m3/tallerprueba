import os
import smtplib
import ssl
from email.message import EmailMessage
from flask import current_app as app
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')


def enviar_codigo_2fa(destinatario: str, codigo: str) -> bool:
    """Envía el código de verificación en dos pasos por correo. Devuelve True si se envió."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        app.logger.error("2FA: faltan GMAIL_USER/GMAIL_APP_PASSWORD en el .env")
        return False

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Código de verificación'
    mensaje['From'] = GMAIL_USER
    mensaje['To'] = destinatario
    mensaje.set_content(
        f"Tu código de verificación es: {codigo}\n\n"
        "Este código vence en 5 minutos. Si no intentaste iniciar sesión, ignorá este mensaje."
    )

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls(context=contexto)
            servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            servidor.send_message(mensaje)
        return True
    except Exception as e:
        app.logger.error(f"2FA: error al enviar el código por correo: {str(e)}")
        return False
