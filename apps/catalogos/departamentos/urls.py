
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import DepartamentosViewSet

router = DefaultRouter()
router.register(r'departamentos', DepartamentosViewSet, basename='departamentos')

app_name = 'departamentos'

urlpatterns = [
    path('', include(router.urls)),
]
