from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import ServicioViewSet

router = DefaultRouter()
router.register(r'servicios', ServicioViewSet, basename='servicios')

app_name = 'servicios'

urlpatterns = [
    path('', include(router.urls)),
]

