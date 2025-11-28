from django.contrib import admin
from .models import Departamentos


@admin.register(Departamentos)
class DepartamentosAdmin(admin.ModelAdmin):
    list_display = ('id', 'Nombre',)   # 👈 quitar 'Descripcion'
    search_fields = ('Nombre',)

from django.contrib import admin

# Register your models here.
