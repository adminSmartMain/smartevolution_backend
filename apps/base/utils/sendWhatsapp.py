import environ
from twilio.rest import Client

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

def sendWhatsApp(message, to, media=None):
    try:
        account_sid = env('TWILIO_ACCOUNT_SID')
        auth_token  = env('TWILIO_AUTH_TOKEN')
        client      = Client(account_sid, auth_token)
        if media:
            message = client.messages.create(from_=f"whatsapp:{env('TWILIO_NUMBER')}",to=f'whatsapp:+{to}',media_url=f'{media}')
        else:
            message = client.messages.create(from_=f"whatsapp:{env('TWILIO_NUMBER')}",body=message,to=f'whatsapp:+{to}')
        return message
    except Exception as e:
        raise e