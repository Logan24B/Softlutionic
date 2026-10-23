from rest_framework import serializers

from .models import LogAuditoria


class LogAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAuditoria
        fields = '__all__'
        read_only_fields = tuple(
            field.name for field in LogAuditoria._meta.fields
        )