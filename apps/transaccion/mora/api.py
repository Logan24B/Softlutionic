from rest_framework import filters, viewsets

from .models import Mora
from .serializers import MoraSerializer


class MoraViewSet(viewsets.ModelViewSet):
    queryset = Mora.objects.select_related(
        'FacturaId',
        'FacturaId__EstadoId',
        'FacturaId__ContratoId',
        'FacturaId__ContratoId__TipoContratoId',
    ).all()
    serializer_class = MoraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['DescripcionMora']
    ordering_fields = ['Fecha_Inicio', 'Hora_Inicio', 'Fecha_Final', 'Hora_Final', 'Monto_Mora', 'id']
    ordering = ['-Fecha_Inicio', '-Hora_Inicio']

    def get_queryset(self):
        from apps.transaccion.factura.services import sincronizar_facturas_vencidas

        sincronizar_facturas_vencidas()
        return super().get_queryset()
