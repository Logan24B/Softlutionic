from django.db import transaction, IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.transaccion.factura.serializers import FacturaSerializer, DetalleFacturaSerializer
from .registry import MODULES, capabilities
from .auth import identity
from .policy import MobileAuthorizationPolicy as Policy
from .serializers import MobileUserSerializer

class MobilePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        action = {'list':'read','retrieve':'read','metadata':'read','create':'create',
                  'update':'update','partial_update':'update','destroy':'delete'}.get(view.action, 'read')
        allowed = capabilities(request.user, view.mobile_name).get(action, False)
        if not allowed and view.mobile_name in Policy.EMPLOYEE_READ_ONLY_MODULES and action != 'read':
            label = {'servicios': 'servicios', 'tipos-contrato': 'tipos de contrato'}[view.mobile_name]
            self.message = f'No tienes permiso para modificar {label}.'
        return allowed

    def has_object_permission(self, request, view, obj):
        if view.mobile_name == 'usuarios':
            Policy.check_user_access(
                request.user, obj, read_only=request.method in permissions.SAFE_METHODS)
        return True

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
    def get_serializer_class(self):
        if self.mobile_name == 'usuarios':
            return MobileUserSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter collections, but retain detail lookup so forbidden targets return 403.
        if self.mobile_name == 'usuarios' and not self.detail:
            return Policy.visible_users(self.request.user, queryset)
        return queryset

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
            if name == 'notificaciones':
                result.append({'name': name, 'permissions': caps, 'fields': []})
                continue
            serializer_class = MobileUserSerializer if name == 'usuarios' else view.serializer_class
            serializer = serializer_class(context={'request': request})
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
