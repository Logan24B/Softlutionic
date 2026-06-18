from rest_framework import serializers

from apps.catalogos.clientes.models import Cliente
from apps.catalogos.clientes.serializers import ClienteSerializer
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    ClienteId = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    cliente_detalle = ClienteSerializer(source='ClienteId', read_only=True)
    estado_descripcion = serializers.CharField(read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'ClienteId',
            'cliente_detalle',
            'Fecha_Envio',
            'Mensaje',
            'EstadoNotificacion',
            'estado_descripcion',
        ]

