from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    search_fields = ('id', 'Nombre1', 'Nombre2', 'Apellido1', 'Apellido2', 'Email', 'Celular')
    list_display  = ('id', 'Nombre1', 'Apellido1', 'Email', 'Estado', 'Fecha')
    list_filter   = ('Estado',)
    date_hierarchy = 'Fecha'
    ordering      = ('id',)
    list_per_page = 25
                 # opcional

