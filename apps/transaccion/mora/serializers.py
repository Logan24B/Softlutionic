from rest_framework import serializers

from apps.transaccion.factura.models import Factura
from apps.transaccion.factura.serializers import FacturaSerializer
from .models import Mora


class MoraSerializer(serializers.ModelSerializer):
    FacturaId = serializers.PrimaryKeyRelatedField(queryset=Factura.objects.all())
    factura_detalle = FacturaSerializer(source='FacturaId', read_only=True)
    estado_descripcion = serializers.CharField(read_only=True)

    class Meta:
        model = Mora
        fields = [
            'id',
            'Fecha_Inicio',
            'Hora_Inicio',
            'Fecha_Final',
            'Hora_Final',
            'Monto_Mora',
            'EstadoMora',
            'estado_descripcion',
            'FacturaId',
            'factura_detalle',
            'DescripcionMora',
        ]

    def validate_Monto_Mora(self, value):
        if value < 0:
            raise serializers.ValidationError('El monto de mora no puede ser negativo.')
        return value

    def validate(self, attrs):
        inicio = attrs.get('Fecha_Inicio', getattr(self.instance, 'Fecha_Inicio', None))
        hora_inicio = attrs.get('Hora_Inicio', getattr(self.instance, 'Hora_Inicio', None))
        final = attrs.get('Fecha_Final', getattr(self.instance, 'Fecha_Final', None))
        hora_final = attrs.get('Hora_Final', getattr(self.instance, 'Hora_Final', None))

        if inicio and final and final < inicio:
            raise serializers.ValidationError('Fecha_Final no puede ser menor que Fecha_Inicio.')

        if (
            inicio
            and final
            and hora_inicio
            and hora_final
            and final == inicio
            and hora_final < hora_inicio
        ):
            raise serializers.ValidationError(
                'Hora_Final no puede ser menor que Hora_Inicio cuando las fechas son iguales.'
            )

        return attrs
