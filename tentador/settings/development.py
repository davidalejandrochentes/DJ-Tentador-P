from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-myj96a53zh1eu^f(z^@5$a50g%qt*0(4!@aehxr0=pc+3))r(8'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuraciones de Telegram
TELEGRAM_BOT_TOKEN = '7565307846:AAF0DHYV4SWB6wO7POLoNRsAL5VW3L0g3Mo'
TELEGRAM_CHAT_ID = '5992843153'