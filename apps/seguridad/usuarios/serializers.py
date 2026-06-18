from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    Email = serializers.EmailField(source='email')
    Usuario = serializers.CharField(source='username', required=False)
    Contrasena = serializers.CharField(
        source='password',
        write_only=True,
        required=False,
        style={'input_type': 'password'},
    )
    rol_descripcion = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'PrimerNombre',
            'SegundoNombre',
            'Email',
            'Usuario',
            'Contrasena',
            'Rol',
            'rol_descripcion',
            'FechaRegistro',
            'HoraRegistro',
            'is_active',
        ]
        read_only_fields = ['id', 'rol_descripcion', 'FechaRegistro', 'HoraRegistro']

    def validate(self, attrs):
        if not attrs.get('username') and attrs.get('email'):
            attrs['username'] = attrs['email']
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'Contrasena': 'La contrasena es obligatoria.'})
        return attrs

    def validate_Contrasena(self, value):
        validate_password(value, self.instance)
        return value

    def validate_PrimerNombre(self, value):
        primer_nombre = value.strip()
        if not primer_nombre:
            raise serializers.ValidationError('El primer nombre es obligatorio.')
        return primer_nombre

    def validate_SegundoNombre(self, value):
        segundo_nombre = value.strip()
        if not segundo_nombre:
            raise serializers.ValidationError('El segundo nombre es obligatorio.')
        return segundo_nombre

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'Contrasena': 'La contrasena es obligatoria.'})

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
