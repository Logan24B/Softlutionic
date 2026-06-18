from rest_framework import serializers

from apps.catalogos.clientes.models import Cliente
from apps.catalogos.clientes.serializers import ClienteSerializer
from .models import Contrato, TipoContrato


class TipoContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoContrato
        fields = [
            'id',
            'Nombre',
            'Descripcion',
        ]

    def validate_Nombre(self, value):
        nombre = value.strip()
        queryset = TipoContrato.objects.filter(Nombre__iexact=nombre)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un tipo de contrato con este nombre.')

        return nombre


class ContratoSerializer(serializers.ModelSerializer):
    ClienteId = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    TipoContratoId = serializers.PrimaryKeyRelatedField(
        queryset=TipoContrato.objects.all(),
        required=False,
        allow_null=True,
    )
    cliente_detalle = ClienteSerializer(source='ClienteId', read_only=True)
    tipo_contrato_detalle = TipoContratoSerializer(source='TipoContratoId', read_only=True)
    estado_descripcion = serializers.SerializerMethodField()

    class Meta:
        model = Contrato
        fields = [
            'id',
            'ClienteId',
            'cliente_detalle',
            'TipoContratoId',
            'tipo_contrato_detalle',
            'Fecha_Inc',
            'Fecha_Fin',
            'EstadoContrato',
            'estado_descripcion',
            'Descripcion',
        ]

    def get_estado_descripcion(self, obj):
        return 'Activo' if obj.EstadoContrato else 'Finalizado'

    def validate(self, attrs):
        fecha_inicio = attrs.get('Fecha_Inc', getattr(self.instance, 'Fecha_Inc', None))
        fecha_fin = attrs.get('Fecha_Fin', getattr(self.instance, 'Fecha_Fin', None))
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError('Fecha_Fin no puede ser menor que Fecha_Inc.')
        return attrs
