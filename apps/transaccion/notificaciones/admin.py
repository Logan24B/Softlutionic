from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ClienteId', 'Fecha_Envio', 'EstadoNotificacion')
    list_filter = ('EstadoNotificacion',)
    search_fields = ('Mensaje', 'ClienteId__Nombre', 'ClienteId__Apellido')
