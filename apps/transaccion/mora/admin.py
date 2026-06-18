from django.contrib import admin

from .models import Mora


@admin.register(Mora)
class MoraAdmin(admin.ModelAdmin):
    list_display = ('id', 'FacturaId', 'Monto_Mora', 'EstadoMora', 'Fecha_Inicio', 'Hora_Inicio', 'Fecha_Final', 'Hora_Final')
    list_filter = ('EstadoMora',)
    search_fields = ('DescripcionMora', 'FacturaId__CodigoFact')
