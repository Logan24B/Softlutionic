from rest_framework import filters, viewsets

from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.select_related('ClienteId').all()
    serializer_class = NotificacionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Mensaje', 'ClienteId__Nombre', 'ClienteId__Apellido']
    ordering_fields = ['Fecha_Envio', 'EstadoNotificacion', 'id']
    ordering = ['-Fecha_Envio']

    def get_queryset(self):
        qs = super().get_queryset()
        leida = self.request.query_params.get('leida')
        if leida is not None:
            qs = qs.filter(EstadoNotificacion=leida.lower() in ['1', 'true', 'si', 'sí'])
        return qs
