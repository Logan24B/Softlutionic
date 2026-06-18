
from rest_framework import serializers
from .models import Departamentos

class DepartamentosSerializer(serializers.ModelSerializer):
    """
    Serializer para la entidad Departamentos.
    Se encarga de convertir entre objeto Python y JSON.
    """

    class Meta:
        model = Departamentos
        fields = ['id', 'Nombre']

    def validate_Nombre(self, value):
        nombre = value.strip()
        queryset = Departamentos.objects.filter(Nombre__iexact=nombre)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un departamento con este nombre.')

        return nombre
