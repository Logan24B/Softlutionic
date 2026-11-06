from rest_framework import serializers
from django.db import transaction

from apps.transaccion.factura.models import Factura
from apps.transaccion.factura.serializers import FacturaSerializer
from .models import Pago


class PagoSerializer(serializers.ModelSerializer):
    FacturaId = serializers.PrimaryKeyRelatedField(queryset=Factura.objects.all())
    factura_detalle = FacturaSerializer(source='FacturaId', read_only=True)
    estado_descripcion = serializers.CharField(read_only=True)
    metodo_descripcion = serializers.CharField(read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id',
            'Fecha_Pago',
            'Monto_Pagado',
            'EstadoPago',
            'estado_descripcion',
            'MetodoPago',
            'metodo_descripcion',
            'FacturaId',
            'factura_detalle',
            'NumeroRecibo',
        ]

    def validate_Monto_Pagado(self, value):
        if value < 0:
            raise serializers.ValidationError('El monto pagado no puede ser negativo.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        pago = super().create(validated_data)

        from apps.transaccion.factura.services import sincronizar_estado_factura

        sincronizar_estado_factura(pago.FacturaId)
        from apps.transaccion.notificaciones.mongo import notify_after_commit
        notify_after_commit(pago)
        return pago

    def update(self, instance, validated_data):
        pago = super().update(instance, validated_data)

        from apps.transaccion.factura.services import sincronizar_estado_factura

        sincronizar_estado_factura(pago.FacturaId)
        return pago
