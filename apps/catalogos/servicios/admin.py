from django.contrib import admin

from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'Nombre_Servicio', 'Precio', 'Duracion')
    search_fields = ('Nombre_Servicio', 'Descripcion')
