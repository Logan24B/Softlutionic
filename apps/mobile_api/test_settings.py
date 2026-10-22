"""Isolated tests: never connects to SQL Server or Azure."""
import os
os.environ.setdefault('SOFTFACTUR_DEBUG', 'true')
from SoftFactur.settings import *
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ALLOWED_HOSTS = ['testserver', 'localhost']
