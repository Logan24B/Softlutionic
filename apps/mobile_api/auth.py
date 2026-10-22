from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import AnonRateThrottle
from apps.seguridad.usuarios.serializers import UserSerializer
from .registry import MODULES, capabilities

def identity(user):
    return {'user': UserSerializer(user).data,
            'permissions': {name: capabilities(user, name) for name in MODULES},
            'dashboard': bool(user.Rol)}

class MobileTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        value = attrs.get('username', '').strip()
        record = get_user_model().objects.filter(Q(username__iexact=value) | Q(email__iexact=value)).first()
        attrs['username'] = record.get_username() if record else value
        data = super().validate(attrs)
        data.update(identity(self.user))
        return data

class LoginThrottle(AnonRateThrottle):
    rate = '10/min'

class LoginView(TokenObtainPairView):
    serializer_class = MobileTokenSerializer
    throttle_classes = [LoginThrottle]
