from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from apps.seguridad.usuarios.models import user

@admin.register(user)
class UserAdmin(UserAdmin):
    pass

# Register your models here.
