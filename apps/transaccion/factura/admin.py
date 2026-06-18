from django.contrib import admin

from .models import DetalleFactura, EstadoFactura, Factura


@admin.register(EstadoFactura)
class EstadoFacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estado')
    search_fields = ('estado',)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'CodigoFact', 'UsuarioId', 'ContratoId', 'EstadoId', 'Fecha_Emision', 'Hora_Emision', 'Fecha_Vencimiento', 'Hora_Vencimiento', 'Monto_Total')
    list_filter = ('EstadoId', 'Fecha_Emision', 'Fecha_Vencimiento')
    search_fields = ('UsuarioId__PrimerNombre', 'UsuarioId__SegundoNombre', 'UsuarioId__email', 'ContratoId__ClienteId__Nombre')


@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'FacturaId', 'ServicioId', 'PrecioVenta')
    search_fields = ('ServicioId__Nombre_Servicio',)
