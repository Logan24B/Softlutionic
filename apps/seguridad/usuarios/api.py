from django.contrib.auth import get_user_model
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserSerializer

User = get_user_model()


class UsuarioWritePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_authenticated and request.user.Rol)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UsuarioWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['PrimerNombre', 'SegundoNombre', 'email', 'username']
    ordering_fields = ['PrimerNombre', 'SegundoNombre', 'email', 'Rol', 'id']
    ordering = ['PrimerNombre', 'SegundoNombre']

    @action(detail=False, methods=['get'])
    def administradores(self, request):
        serializer = self.get_serializer(self.get_queryset().filter(Rol=True), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def empleados(self, request):
        serializer = self.get_serializer(self.get_queryset().filter(Rol=False), many=True)
        return Response(serializer.data)
