
from rest_framework import viewsets, filters
from .models import Departamentos
from .serializers import DepartamentosSerializer


class DepartamentosViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Departamentos basado en ModelViewSet.

    Proporciona automáticamente:
    - GET    /departamentos/        → list
    - POST   /departamentos/        → create
    - GET    /departamentos/{id}/   → retrieve
    - PUT    /departamentos/{id}/   → update
    - PATCH  /departamentos/{id}/   → partial_update
    - DELETE /departamentos/{id}/   → destroy
    """

    queryset = Departamentos.objects.all().order_by('Nombre')
    serializer_class = DepartamentosSerializer

    # Opcional: búsqueda y ordenamiento
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Nombre']          # /departamentos/?search=Managua
    ordering_fields = ['Nombre', 'id']  # /departamentos/?ordering=Nombre
    ordering = ['Nombre']
