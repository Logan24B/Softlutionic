"""Mobile identity and user writes without changing web serializers."""
from rest_framework import serializers
from apps.seguridad.usuarios.serializers import UserSerializer
from .policy import MobileAuthorizationPolicy as Policy


class MobileUserSerializer(UserSerializer):
    is_superuser = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    rol_descripcion = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['is_superuser', 'is_staff']
        read_only_fields = UserSerializer.Meta.read_only_fields + ['is_superuser', 'is_staff']

    def get_rol_descripcion(self, obj):
        return Policy.role(obj)

    def to_internal_value(self, data):
        # Reject protected attributes even when other input fields are invalid.
        if {'is_superuser', 'is_staff'}.intersection(data):
            Policy.check_payload(self.context['request'].user, data, self.instance is None)
        return super().to_internal_value(data)

    def validate(self, attrs):
        actor = self.context['request'].user
        if self.instance is not None:
            Policy.check_target(actor, self.instance)
        Policy.check_payload(actor, attrs, self.instance is None)
        return super().validate(attrs)
