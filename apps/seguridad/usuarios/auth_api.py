import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        usuario = str(request.data.get('usuario') or request.data.get('Usuario') or '').strip()
        contrasena = str(request.data.get('contrasena') or request.data.get('Contrasena') or '')

        if not usuario or not contrasena:
            return Response(
                {'detail': 'Ingrese usuario/correo y contrasena.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_record = User.objects.filter(
            Q(username__iexact=usuario) | Q(email__iexact=usuario)
        ).first()
        username = user_record.get_username() if user_record else usuario
        user = authenticate(request, username=username, password=contrasena)

        if user is None or not user.is_active:
            return Response(
                {'detail': 'Usuario o contrasena incorrectos.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response({'user': UserSerializer(user).data})


class SessionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'authenticated': True, 'user': UserSerializer(request.user).data})


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Sesion cerrada correctamente.'})


class PasswordResetRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get('email') or request.data.get('Email') or '').strip()
        if not email:
            return Response(
                {'detail': 'Ingrese el correo electronico registrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                f'/frontend/Softlutionic/login.html?uid={uid}&token={token}'
            )
            try:
                send_mail(
                    'Recuperacion de contrasena - SoftFactur',
                    (
                        'Se solicito restablecer la contrasena de su cuenta en SoftFactur.\n\n'
                        f'Abra este enlace para crear una nueva contrasena:\n{reset_url}\n\n'
                        'Si usted no solicito este cambio, ignore este correo.'
                    ),
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@softfactur.local'),
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception('No se pudo enviar el correo de recuperacion de contrasena.')

        return Response({
            'detail': 'Si el correo esta registrado, recibira un enlace de recuperacion.'
        })


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        nueva_contrasena = str(
            request.data.get('nueva_contrasena') or request.data.get('Contrasena') or ''
        )

        if not uid or not token or not nueva_contrasena:
            return Response(
                {'detail': 'El enlace y la nueva contrasena son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'El enlace de recuperacion no es valido o ya expiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validate_password(nueva_contrasena, user)
        user.set_password(nueva_contrasena)
        user.save()
        return Response({'detail': 'Contrasena actualizada correctamente.'})
