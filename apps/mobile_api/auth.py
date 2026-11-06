from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import AnonRateThrottle
from .serializers import MobileUserSerializer
from .policy import MobileAuthorizationPolicy as Policy
from .registry import MOBILE_NAMES, capabilities

def identity(user):
    return {'user': MobileUserSerializer(user).data,
            'permissions': {name: capabilities(user, name) for name in MOBILE_NAMES},
            'dashboard': Policy.is_admin(user)}

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
