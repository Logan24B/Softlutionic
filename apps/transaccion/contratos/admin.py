from django.contrib import admin

from .models import Contrato, TipoContrato


@admin.register(TipoContrato)
class TipoContratoAdmin(admin.ModelAdmin):
    list_display = ('id', 'Nombre', 'Descripcion')
    search_fields = ('Nombre', 'Descripcion')


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('id', 'ClienteId', 'TipoContratoId', 'Fecha_Inc', 'Fecha_Fin', 'EstadoContrato')
    list_filter = ('EstadoContrato', 'TipoContratoId')
    search_fields = ('Descripcion', 'ClienteId__Nombre', 'ClienteId__Apellido', 'TipoContratoId__Nombre')
