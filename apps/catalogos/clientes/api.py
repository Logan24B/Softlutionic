from django.shortcuts import render

# Create your views here.
# clientes/api.py
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet basado en ModelViewSet:
    - Proporciona CRUD completo de forma automática:
      * list    -> GET /clientes/
      * retrieve -> GET /clientes/{id}/
      * create   -> POST /clientes/
      * update   -> PUT /clientes/{id}/
      * partial_update -> PATCH /clientes/{id}/
      * destroy  -> DELETE /clientes/{id}/

    Además, aquí podemos agregar 'extras' como:
    - Búsqueda (search)
    - Ordenamiento (ordering)
    - Acciones personalizadas (activar/desactivar cliente)
    """

    # Query base: traemos todos los clientes
    queryset = Cliente.objects.all()

    # Serializer que se usará para convertir los datos
    serializer_class = ClienteSerializer

    # Filtros de DRF: permiten buscar y ordenar desde la URL
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # Campos que se pueden buscar, por ejemplo:
    # GET /clientes/?search=Juan
    search_fields = ['Nombre1', 'Apellido1', 'Email', 'Celular']

    # Campos por los que se puede ordenar:
    # GET /clientes/?ordering=Nombre1
    # GET /clientes/?ordering=-Fecha  (orden descendente)
    ordering_fields = ['Nombre1', 'Apellido1', 'Fecha', 'Estado']
    # Orden por defecto:
    ordering = ['Nombre1']

    def get_queryset(self):
        """
        Permite filtrar la lista según parámetros de la URL.
        Por ejemplo, filtrar solo clientes activos:
        GET /clientes/?activo=true
        """
        qs = super().get_queryset()
        activo = self.request.query_params.get('activo')

        if activo is not None:
            # 'true'/'false' en minúsculas para mayor tolerancia
            activo = activo.lower()
            if activo in ['true', '1', 't', 'sí', 'si']:
                qs = qs.filter(Estado=True)
            elif activo in ['false', '0', 'f', 'no']:
                qs = qs.filter(Estado=False)

        return qs

    # ---------- ACCIONES PERSONALIZADAS ----------

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Acción personalizada:
        - URL: POST /clientes/{id}/activar/
        - Propósito: marcar un cliente como activo (Estado=True)
        """
        cliente = self.get_object()
        cliente.Estado = True
        cliente.save()
        serializer = self.get_serializer(cliente)
        return Response(
            {
                "mensaje": "Cliente activado correctamente.",
                "cliente": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Acción personalizada:
        - URL: POST /clientes/{id}/desactivar/
        - Propósito: marcar un cliente como inactivo (Estado=False)
        """
        cliente = self.get_object()
        cliente.Estado = False
        cliente.save()
        serializer = self.get_serializer(cliente)
        return Response(
            {
                "mensaje": "Cliente desactivado correctamente.",
                "cliente": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        Acción de colección (no por id):
        - URL: GET /clientes/activos/
        - Devuelve únicamente clientes con Estado=True
        """
        clientes_activos = self.get_queryset().filter(Estado=True)
        page = self.paginate_queryset(clientes_activos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(clientes_activos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
