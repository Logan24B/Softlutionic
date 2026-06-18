from rest_framework import filters, viewsets

from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Nombre', 'Apellido', 'Cedula', 'Correo', 'Direccion']
    ordering_fields = ['Nombre', 'Apellido', 'FechaRegistro', 'id']
    ordering = ['Nombre', 'Apellido']
