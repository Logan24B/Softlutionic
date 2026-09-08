from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.catalogos.servicios.models import Servicio
from apps.catalogos.servicios.serializers import ServicioSerializer
from apps.seguridad.usuarios.serializers import UserSerializer
from apps.transaccion.contratos.models import Contrato
from apps.transaccion.contratos.serializers import ContratoSerializer
from .models import DetalleFactura, EstadoFactura, Factura

User = get_user_model()


class EstadoFacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoFactura
        fields = [
            'id',
            'estado',
        ]


class DetalleFacturaSerializer(serializers.ModelSerializer):
    FacturaId = serializers.PrimaryKeyRelatedField(queryset=Factura.objects.all())
    ServicioId = serializers.PrimaryKeyRelatedField(queryset=Servicio.objects.all())
    PrecioVenta = serializers.IntegerField(required=False)
    Subtotal = serializers.IntegerField(read_only=True)
    servicio_detalle = ServicioSerializer(source='ServicioId', read_only=True)

    class Meta:
        model = DetalleFactura
        fields = [
            'id',
            'FacturaId',
            'ServicioId',
            'servicio_detalle',
            'PrecioVenta',
            'Cantidad',
            'Subtotal',
        ]

    def validate_PrecioVenta(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio de venta no puede ser negativo.')
        return value

    def validate_Cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor que cero.')
        return value

    def create(self, validated_data):
        if 'PrecioVenta' not in validated_data:
            validated_data['PrecioVenta'] = validated_data['ServicioId'].Precio
        return super().create(validated_data)

    def update(self, instance, validated_data):
        servicio_cambiado = (
            'ServicioId' in validated_data
            and validated_data['ServicioId'] != instance.ServicioId
        )

        if servicio_cambiado and 'PrecioVenta' not in validated_data:
            validated_data['PrecioVenta'] = validated_data['ServicioId'].Precio

        return super().update(instance, validated_data)


class FacturaSerializer(serializers.ModelSerializer):
    UsuarioId = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    ContratoId = serializers.PrimaryKeyRelatedField(queryset=Contrato.objects.all())
    EstadoId = serializers.PrimaryKeyRelatedField(
        queryset=EstadoFactura.objects.all(),
        required=False,
    )
    usuario_detalle = UserSerializer(source='UsuarioId', read_only=True)
    contrato_detalle = ContratoSerializer(source='ContratoId', read_only=True)
    estado_detalle = EstadoFacturaSerializer(source='EstadoId', read_only=True)
    cliente_detalle = serializers.SerializerMethodField()
    detalles = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = [
            'id',
            'UsuarioId',
            'usuario_detalle',
            'ContratoId',
            'contrato_detalle',
            'cliente_detalle',
            'EstadoId',
            'estado_detalle',
            'Fecha_Emision',
            'Hora_Emision',
            'Fecha_Vencimiento',
            'Hora_Vencimiento',
            'Monto_Total',
            'CodigoFact',
            'detalles',
        ]
        read_only_fields = ['Fecha_Vencimiento', 'Hora_Vencimiento', 'Monto_Total', 'detalles']

    def get_cliente_detalle(self, obj):
        cliente = getattr(getattr(obj, 'ContratoId', None), 'ClienteId', None)
        if not cliente:
            return None

        return {
            'id': cliente.id,
            'Nombre': cliente.Nombre,
            'Apellido': cliente.Apellido,
            'Correo': cliente.Correo,
            'Telefono': cliente.Telefono,
        }

    def validate(self, attrs):
        emision = attrs.get('Fecha_Emision', getattr(self.instance, 'Fecha_Emision', None))
        hora_emision = attrs.get('Hora_Emision', getattr(self.instance, 'Hora_Emision', None))
        vencimiento = attrs.get('Fecha_Vencimiento', getattr(self.instance, 'Fecha_Vencimiento', None))
        hora_vencimiento = attrs.get('Hora_Vencimiento', getattr(self.instance, 'Hora_Vencimiento', None))

        if emision and vencimiento and vencimiento < emision:
            raise serializers.ValidationError(
                'Fecha_Vencimiento no puede ser menor que Fecha_Emision.'
            )

        if (
            emision
            and vencimiento
            and hora_emision
            and hora_vencimiento
            and vencimiento == emision
            and hora_vencimiento < hora_emision
        ):
            raise serializers.ValidationError(
                'Hora_Vencimiento no puede ser menor que Hora_Emision cuando las fechas son iguales.'
            )

        return attrs

    def create(self, validated_data):
        from .services import ESTADO_PENDIENTE, obtener_estado

        validated_data.pop('EstadoId', None)
        validated_data['EstadoId'] = obtener_estado(ESTADO_PENDIENTE)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('Fecha_Emision', None)
        validated_data.pop('Hora_Emision', None)
        validated_data.pop('EstadoId', None)

        factura = super().update(instance, validated_data)

        from .services import sincronizar_estado_factura

        return sincronizar_estado_factura(factura)
