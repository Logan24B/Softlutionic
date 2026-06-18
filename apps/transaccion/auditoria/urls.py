from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import LogAuditoriaViewSet

router = DefaultRouter()
router.register(r'auditoria', LogAuditoriaViewSet, basename='auditoria')

app_name = 'auditoria'

urlpatterns = [
    path('', include(router.urls)),
]

