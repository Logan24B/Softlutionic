from rest_framework import serializers

from .models import Servicio


class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

    def validate_Nombre_Servicio(self, value):
        nombre = value.strip()
        queryset = Servicio.objects.filter(Nombre_Servicio__iexact=nombre)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un servicio con este nombre.')

        return nombre

    def validate_Precio(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio no puede ser negativo.')
        return value
