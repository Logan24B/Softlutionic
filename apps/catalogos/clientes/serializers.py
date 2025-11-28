# clientes/serializers.py
from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer:
    - Convierte instancias de Cliente a JSON y viceversa.
    - Valida los datos que llegan por la API.
    """

    class Meta:
        model = Cliente
        # '__all__' incluye todos los campos del modelo
        fields = '__all__'

    # Ejemplo de validación específica de un campo
    def validate_Email(self, value):
        """
        Valida el campo Email.
        Aquí aplicamos reglas adicionales más allá del 'unique=True'.
        """
        if not value.endswith(('.com', '.org', '.net', '.ni')):
            raise serializers.ValidationError(
                "El correo debe tener un dominio válido (.com, .org, .net, .ni, etc.)."
            )
        return value

    # Ejemplo de validación general (a nivel de registro)
    def validate(self, attrs):
        """
        Se ejecuta después de validar campo por campo.
        Permite reglas que dependen de varios campos a la vez.
        """
        nombre1 = attrs.get('Nombre1')
        apellido1 = attrs.get('Apellido1')

        if nombre1 and apellido1 and nombre1 == apellido1:
            raise serializers.ValidationError(
                "El primer nombre y el primer apellido no pueden ser idénticos."
            )

        return attrs
