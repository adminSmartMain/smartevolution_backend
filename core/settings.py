from pathlib import Path
from datetime import timedelta
import environ
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG =  True if env('DEBUG') == 'True' else False


# --- SEGURIDAD DE HOSTS ---
# Solo a dominios oficiales de Smart Evolution
ALLOWED_HOSTS = [
    "devapp.smartevolution.com.co", 
    "app.smartevolution.com.co",
    "apis.smartevolution.com.co",
    "localhost",
    "127.0.0.1",
    "0.0.0.0", 
]

# number format
USE_DECIMAL_SEPARATOR = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."

DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

# Application definition

BASE_APPS = ['django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.humanize' ]

LOCAL_APPS = ['apps.base',
            'apps.authentication',
            'apps.misc',
            'apps.client',
            'apps.bill', 
            'apps.report', 
            'apps.operation',
            'apps.administration', ]

THIRD_PARTY_APPS = ['rest_framework',
                     'drf_spectacular',
                    'rest_framework.authtoken',
                    'corsheaders',
                    'gunicorn',
                    'django_crontab',
                    'import_export'
                    ]

INSTALLED_APPS = BASE_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# --- SEGURIDAD CSRF ---
# Lista de orígenes confiables para el envío de formularios y peticiones de estado
CSRF_TRUSTED_ORIGINS = [
    'http://3.93.44.58:5000',
    'https://apis.smartevolution.com.co',
    # Agrega otras URLs de confianza si es necesario
]

CRONJOBS = [
    ('*/10 * * * *', 'apps.base.cron.check_bills_by_cufe >> /app/logs/cronjob.log 2>&1'),
    #('0 */6 * * *', 'apps.base.cron.check_bills_by_cufe >> /app/logs/cronjob.log 2>&1'),
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['apps.base.templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env('ENGINE'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS':{
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
            }
    }
}



# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication', ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.base.exceptions.custom_exception_handler',
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart Evolution API',
    'DESCRIPTION': (
        'Documentación técnica de los endpoints consumidos por el frontend de Smart Evolution. '
        'La autenticación se realiza con JWT usando el encabezado Authorization: Bearer <token>.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    # Esquema Bearer para que Swagger muestre el botón Authorize.
    # Aunque simplejwt suele detectarse, esto lo deja explícito y estable.
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'SECURITY': [{'BearerAuth': []}],
    'SCHEMA_PATH_PREFIX': '/api',
    'TAGS': [
        {'name': 'Autenticación', 'description': 'Inicio de sesión, registro y recuperación de contraseña.'},
        {'name': 'Usuarios', 'description': 'Administración y roles de usuarios.'},
        {'name': 'Clientes', 'description': 'Clientes, contactos, representantes, cuentas y perfiles.'},
        {'name': 'Catálogos', 'description': 'Catálogos base: ciudades, bancos, tipos, CIIU, países y similares.'},
        {'name': 'Facturas', 'description': 'Gestión y lectura de facturas.'},
        {'name': 'Operaciones', 'description': 'Preoperaciones, operaciones masivas, borradores y consultas operativas.'},
        {'name': 'Recaudos', 'description': 'Registro individual, registro masivo, validación Excel e historial de recaudos.'},
        {'name': 'Administración', 'description': 'Depósitos, egresos, devoluciones y movimientos administrativos.'},
        {'name': 'Reportes', 'description': 'Órdenes, recibos, resúmenes y documentos generados.'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
    },
}



# JWT settings
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=73000)
}

# --- CONFIGURACIÓN DE COOKIES Y SEGURIDAD HTTP ---

if not DEBUG:
    # Fuerza a que las cookies solo se envíen por HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Protecciones adicionales del navegador
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # HSTS (Seguridad estricta de transporte)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Asegura que Django confíe en el encabezado X-Forwarded-Proto enviado por Nginx
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- CONFIGURACIÓN DE CORS ---
# Los orígenes que pueden consumir la API
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    "https://devapp.smartevolution.com.co", 
    "https://app.smartevolution.com.co",
]

# Para Docker si estamos en modo DEBUG
if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
# SMTP settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = f'{env("EMAIL_HOST_PASSWORD")}'


# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# S3 settings
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = 'us-east-1'
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = 'public-read'

# Aumentar el límite de tamaño para datos en memoria (2.5MB -> 25MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25 MB en bytes

# También puedes aumentar el límite para campos individuales
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
