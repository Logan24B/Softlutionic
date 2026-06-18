from rest_framework import filters, viewsets

from .models import LogAuditoria
from .serializers import LogAuditoriaSerializer


class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogAuditoria.objects.all()
    serializer_class = LogAuditoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Tabla', 'Accion', 'Usuario', 'Detalle']
    ordering_fields = ['Tabla', 'Accion', 'Usuario', 'Fecha', 'IdLog']
    ordering = ['-Fecha']

    def get_queryset(self):
        qs = super().get_queryset()
        tabla = self.request.query_params.get('tabla')
        accion = self.request.query_params.get('accion')
        usuario = self.request.query_params.get('usuario')
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')

        if tabla:
            qs = qs.filter(Tabla__icontains=tabla)
        if accion:
            qs = qs.filter(Accion__icontains=accion)
        if usuario:
            qs = qs.filter(Usuario__icontains=usuario)
        if fecha_desde:
            qs = qs.filter(Fecha__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(Fecha__date__lte=fecha_hasta)
        return qs

