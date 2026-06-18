from rest_framework import filters, viewsets

from .models import Contrato, TipoContrato
from .serializers import ContratoSerializer, TipoContratoSerializer


class TipoContratoViewSet(viewsets.ModelViewSet):
    queryset = TipoContrato.objects.all()
    serializer_class = TipoContratoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Nombre', 'Descripcion']
    ordering_fields = ['Nombre', 'id']
    ordering = ['Nombre']


class ContratoViewSet(viewsets.ModelViewSet):
    queryset = Contrato.objects.select_related('ClienteId', 'TipoContratoId').all()
    serializer_class = ContratoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Descripcion', 'ClienteId__Nombre', 'ClienteId__Apellido', 'TipoContratoId__Nombre']
    ordering_fields = ['Fecha_Inc', 'Fecha_Fin', 'EstadoContrato', 'id']
    ordering = ['-Fecha_Inc']

    def get_queryset(self):
        qs = super().get_queryset()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(EstadoContrato=activo.lower() in ['1', 'true', 'si'])

        cliente = self.request.query_params.get('cliente')
        if cliente:
            qs = qs.filter(ClienteId=cliente)

        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(TipoContratoId=tipo)

        return qs
