# clientes/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ClienteViewSet

# El router se encarga de generar las rutas típicas de un CRUD
router = DefaultRouter()
# 'clientes' será el prefijo de la URL, y 'ClienteViewSet' la lógica
router.register(r'clientes', ClienteViewSet, basename='cliente')

urlpatterns = [
    # Incluimos todas las rutas generadas por el router
    path('', include(router.urls)),
]
