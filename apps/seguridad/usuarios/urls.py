from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import UserViewSet
from .auth_api import (
    LoginAPIView,
    LogoutAPIView,
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    SessionAPIView,
)

router = DefaultRouter()
router.register(r'usuarios', UserViewSet, basename='usuarios')

app_name = 'usuarios'

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='auth_login'),
    path('auth/session/', SessionAPIView.as_view(), name='auth_session'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth_logout'),
    path('auth/password-reset/', PasswordResetRequestAPIView.as_view(), name='password_reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('', include(router.urls)),
]
