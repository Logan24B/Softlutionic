from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('IdLog', 'Tabla', 'Accion', 'Usuario', 'Host', 'Fecha')
    list_filter = ('Tabla', 'Accion')
    search_fields = ('Tabla', 'Accion', 'Usuario', 'Detalle')
    readonly_fields = ('IdLog', 'Tabla', 'Accion', 'ClavePrincipal', 'Usuario', 'Host', 'Fecha', 'Detalle')
