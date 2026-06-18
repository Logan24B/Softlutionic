from rest_framework import serializers
import re

from apps.catalogos.departamentos.models import Departamentos
from apps.catalogos.departamentos.serializers import DepartamentosSerializer
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    DepartamentoId = serializers.PrimaryKeyRelatedField(queryset=Departamentos.objects.all())
    Cedula = serializers.CharField(required=True, allow_blank=False, max_length=20)
    departamento_detalle = DepartamentosSerializer(source='DepartamentoId', read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id',
            'DepartamentoId',
            'departamento_detalle',
            'Nombre',
            'Apellido',
            'Cedula',
            'Telefono',
            'Direccion',
            'FechaRegistro',
            'HoraRegistro',
            'Correo',
            'Estado',
        ]
        read_only_fields = ['id', 'departamento_detalle', 'FechaRegistro', 'HoraRegistro']

    def validate_Telefono(self, value):
        telefono = value.strip()
        digitos = re.sub(r'\D', '', telefono)

        if len(digitos) == 8:
            digitos = f'505{digitos}'

        if len(digitos) != 11 or not digitos.startswith('505'):
            raise serializers.ValidationError('El telefono debe tener formato nicaraguense: +505 0000 0000.')

        telefono_normalizado = f'+505 {digitos[3:7]} {digitos[7:11]}'

        queryset = Cliente.objects.all()

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        for cliente in queryset.only('Telefono'):
            if re.sub(r'\D', '', cliente.Telefono) == digitos:
                raise serializers.ValidationError('Ya existe un cliente con este telefono.')

        return telefono_normalizado

    def validate_Cedula(self, value):
        cedula = value.strip().upper()
        queryset = Cliente.objects.filter(Cedula__iexact=cedula)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un cliente con esta cedula.')

        return cedula

    def validate_Correo(self, value):
        correo = value.strip().lower()
        queryset = Cliente.objects.filter(Correo__iexact=correo)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError('Ya existe un cliente con este correo.')

        return correo
