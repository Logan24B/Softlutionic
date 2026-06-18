from rest_framework import filters, viewsets

from .models import Servicio
from .serializers import ServicioSerializer


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Nombre_Servicio', 'Descripcion', 'Duracion']
    ordering_fields = ['Nombre_Servicio', 'Precio', 'id']
    ordering = ['Nombre_Servicio']

