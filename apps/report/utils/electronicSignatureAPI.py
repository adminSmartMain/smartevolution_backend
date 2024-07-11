
# Utils 
import requests
import environ

env = environ.Env()
environ.Env.read_env()

API_URL         = env('AUCO_API_PROD_URL')

AUCO_USER_EMAIL = env('AUCO_USER_EMAIL')

PRIVATE_HEADERS = {
    'Authorization' :  env('PRIVATE_KEY'),
    'Content-Type'  :  'application/json'
}

PUBLIC_HEADERS  = {
    'Authorization' :  env('PUBLIC_KEY'),
    'Content-Type'  :  'application/json'
}

def genElectronicSignature(base64PDF, name, message, subject, signProfiles):
    
    body = {
        'name'       : name,
        'email'      : AUCO_USER_EMAIL,
        'message'    : message,
        'subject'    : subject,
        'signProfile': signProfiles,
        'file'       : str(base64PDF['pdf']),
        'otpCode' :True,
        'options'    : {
            'whatsapp':True,
        }
    }
    # Gen signature request
    res = requests.post(API_URL + '/document/upload', json=body, headers=PRIVATE_HEADERS)

    # Get response status
    if res.status_code == 200:
        return {
            'error': False,
            'message': res.json()
        }
    else:
        return {
            'error': True,
            'message': res.json()
        }
    

def getSignatureStatus(code):
    # Get signature status
    res = requests.get(API_URL + f'/document?code={code}', headers=PUBLIC_HEADERS)

    # Get response status
    if res.status_code == 200:
        return {
            'error': False,
            'message': res.json()
        }
    else:
        return {
            'error': True,
            'message': res.json()
        }