from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'Nombre', 'Apellido', 'Cedula', 'DepartamentoId', 'Telefono', 'Correo', 'FechaRegistro', 'HoraRegistro')
    search_fields = ('Nombre', 'Apellido', 'Cedula', 'Correo', 'DepartamentoId__Nombre')
    ordering = ('Nombre', 'Apellido')
