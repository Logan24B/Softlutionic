from django.db import transaction, IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.transaccion.factura.serializers import FacturaSerializer, DetalleFacturaSerializer
from .registry import MODULES, capabilities
from .auth import identity

class MobilePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        action = {'list':'read','retrieve':'read','metadata':'read','create':'create',
                  'update':'update','partial_update':'update','destroy':'delete'}.get(view.action, 'read')
        return capabilities(request.user, view.mobile_name).get(action, False)

class AtomicInvoiceSerializer(FacturaSerializer):
    UsuarioId = serializers.HiddenField(default=serializers.CurrentUserDefault())
    lineas = serializers.ListField(child=serializers.DictField(), write_only=True, required=True, allow_empty=False)
    class Meta(FacturaSerializer.Meta):
        fields = FacturaSerializer.Meta.fields + ['lineas']
    def create(self, validated_data):
        lines = validated_data.pop('lineas')
        validated_data['UsuarioId'] = self.context['request'].user
        invoice = super().create(validated_data)
        self.save_lines(invoice, lines)
        return invoice
    def update(self, instance, validated_data):
        lines = validated_data.pop('lineas', None)
        validated_data.pop('UsuarioId', None)
        invoice = super().update(instance, validated_data)
        if lines is not None:
            for detail in list(invoice.detalles.all()):
                detail.delete()
            self.save_lines(invoice, lines)
        return invoice
    def save_lines(self, invoice, lines):
        for line in lines:
            data = {k: v for k, v in line.items() if k in {'ServicioId', 'PrecioVenta', 'Cantidad'}}
            data['FacturaId'] = invoice.pk
            serializer = DetalleFacturaSerializer(data=data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        invoice.refresh_from_db()

class MobileMixin:
    authentication_classes = [JWTAuthentication]
    permission_classes = [MobilePermission]
    pagination_class = None
    def handle_exception(self, exc):
        if isinstance(exc, (ProtectedError, IntegrityError)):
            return Response({'detail': 'El registro tiene dependencias o un valor duplicado.'}, status=409)
        return super().handle_exception(exc)
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(identity(request.user))

class SchemaView(MeView):
    def get(self, request):
        from rest_framework.relations import PrimaryKeyRelatedField
        result = []
        model_routes = {v.queryset.model: k for k, v in MODULES.items()}
        for name, view in MODULES.items():
            caps = capabilities(request.user, name)
            if not caps['read']:
                continue
            serializer = view.serializer_class(context={'request': request})
            fields = []
            for key, field in serializer.fields.items():
                if field.read_only or key in {'UsuarioId', 'EstadoId'} and name == 'facturas':
                    continue
                item = {'name': key, 'label': str(field.label), 'required': field.required,
                        'type': field.__class__.__name__, 'max_length': getattr(field, 'max_length', None)}
                if isinstance(field, PrimaryKeyRelatedField):
                    item['relation'] = model_routes.get(field.queryset.model)
                fields.append(item)
            result.append({'name': name, 'permissions': caps, 'fields': fields})
        return Response(result)
