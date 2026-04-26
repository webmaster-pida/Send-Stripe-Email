import os
import smtplib
from email.message import EmailMessage
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# Variables de entorno (Las configuraremos en Cloud Run)
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
EMAIL_SENDER = os.environ.get('EMAIL_SENDER')       # ej. notificaciones@tudominio.com
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')   # La contraseña de aplicación de 16 caracteres
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')   # A quién le llega el aviso (puede ser tu correo)

def send_email(customer_email, subscription_id):
    """Función para enviar el correo vía SMTP de Gmail"""
    msg = EmailMessage()
    msg.set_content(f"¡Buenas noticias! Tienes una nueva suscripción.\n\n"
                    f"Email del cliente: {customer_email}\n"
                    f"ID de Suscripción: {subscription_id}\n")

    msg['Subject'] = '🚀 Nueva Suscripción en Stripe'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        # Conexión al servidor SMTP de Google
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error enviando correo: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        # Verificamos que la petición venga realmente de Stripe (Seguridad crucial)
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload inválido
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        return jsonify({'error': 'Invalid signature'}), 400

    # Procesamos solo el evento de nueva suscripción
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        # Opcional: Si quieres obtener el email del cliente, deberías usar la API de Stripe aquí
        # stripe.api_key = os.environ.get('STRIPE_API_KEY')
        # customer = stripe.Customer.retrieve(customer_id)
        # customer_email = customer.email

        # Para este ejemplo, enviaremos el ID del customer
        send_email(customer_id, subscription_id)

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
