from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import ContratoViewSet, TipoContratoViewSet

router = DefaultRouter()
router.register(r'tipos-contrato', TipoContratoViewSet, basename='tipos-contrato')
router.register(r'contratos', ContratoViewSet, basename='contratos')

app_name = 'contratos'

urlpatterns = [
    path('', include(router.urls)),
]
