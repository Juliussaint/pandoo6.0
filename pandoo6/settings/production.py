from .base import *

SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['pandoo.megageniusdigital.com', 'www.pandoo.megageniusdigital.com', 'pandoo.com', 'www.pandoo.com']

