from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import NotificacionViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificaciones')

app_name = 'notificaciones'

urlpatterns = [
    path('', include(router.urls)),
]

