from rest_framework import filters, viewsets

from .models import Pago
from .serializers import PagoSerializer


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.select_related('FacturaId', 'FacturaId__ContratoId').all()
    serializer_class = PagoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['FacturaId__CodigoFact']
    ordering_fields = ['Fecha_Pago', 'Monto_Pagado', 'EstadoPago', 'MetodoPago', 'NumeroRecibo']
    ordering = ['-Fecha_Pago']

    def get_queryset(self):
        qs = super().get_queryset()
        confirmado = self.request.query_params.get('confirmado')
        if confirmado is not None:
            qs = qs.filter(EstadoPago=confirmado.lower() in ['1', 'true', 'si', 'sí'])
        return qs

