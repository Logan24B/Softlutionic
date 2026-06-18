from rest_framework import filters, viewsets

from .models import DetalleFactura, EstadoFactura, Factura
from .serializers import DetalleFacturaSerializer, EstadoFacturaSerializer, FacturaSerializer


class EstadoFacturaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstadoFactura.objects.all()
    serializer_class = EstadoFacturaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['estado']
    ordering_fields = ['id', 'estado']
    ordering = ['id']


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = (
        Factura.objects
        .select_related('UsuarioId', 'ContratoId', 'ContratoId__ClienteId', 'EstadoId')
        .prefetch_related('detalles', 'detalles__ServicioId')
        .all()
    )
    serializer_class = FacturaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'CodigoFact',
        'UsuarioId__PrimerNombre',
        'UsuarioId__SegundoNombre',
        'UsuarioId__email',
        'ContratoId__ClienteId__Nombre',
        'EstadoId__estado',
    ]
    ordering_fields = ['Fecha_Emision', 'Hora_Emision', 'Fecha_Vencimiento', 'Hora_Vencimiento', 'Monto_Total', 'CodigoFact', 'EstadoId__estado']
    ordering = ['-Fecha_Emision', '-Hora_Emision']

    def get_queryset(self):
        from .services import sincronizar_facturas_vencidas

        sincronizar_facturas_vencidas()
        return super().get_queryset()


class DetalleFacturaViewSet(viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.select_related('FacturaId', 'ServicioId').all()
    serializer_class = DetalleFacturaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['FacturaId__CodigoFact', 'ServicioId__Nombre_Servicio']
    ordering_fields = ['id', 'PrecioVenta']
    ordering = ['id']
