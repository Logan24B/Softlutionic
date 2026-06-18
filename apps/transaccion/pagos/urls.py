from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import PagoViewSet

router = DefaultRouter()
router.register(r'pagos', PagoViewSet, basename='pagos')

app_name = 'pagos'

urlpatterns = [
    path('', include(router.urls)),
]

