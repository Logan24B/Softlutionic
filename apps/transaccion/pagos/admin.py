from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'NumeroRecibo', 'FacturaId', 'Monto_Pagado', 'EstadoPago', 'MetodoPago')
    list_filter = ('EstadoPago', 'MetodoPago')
    search_fields = ('NumeroRecibo', 'FacturaId__CodigoFact')
