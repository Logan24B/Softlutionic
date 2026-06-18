from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import MoraViewSet

router = DefaultRouter()
router.register(r'moras', MoraViewSet, basename='moras')

app_name = 'mora'

urlpatterns = [
    path('', include(router.urls)),
]

