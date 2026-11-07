from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.dashboard.api import DashboardFacturacionAPIView, DashboardClientesServiciosAPIView
from .auth import LoginView
from .api import MeView, SchemaView, MobileMixin, AtomicInvoiceSerializer
from .registry import MODULES, CONTACT_MODULE
from .notifications import NotificationViewSet
from .contact_requests import ContactRequestViewSet
from .push import PushDeviceView
from .contact_push import ContactPushView
router = DefaultRouter()
router.register(CONTACT_MODULE, ContactRequestViewSet, basename='mobile-contact-requests')
for name, original in MODULES.items():
    if name == 'notificaciones':
        router.register(name, NotificationViewSet, basename='mobile-' + name)
        continue
    attrs = {'mobile_name': name, '__module__': __name__}
    if name == 'facturas':
        attrs['serializer_class'] = AtomicInvoiceSerializer
    cls = type('Mobile' + original.__name__, (MobileMixin, original), attrs)
    router.register(name, cls, basename='mobile-' + name)
urlpatterns = [
 path('push/contact/', ContactPushView.as_view()),
 path('push/devices/', PushDeviceView.as_view()),
 path('push/devices/unregister/', PushDeviceView.as_view(unregister=True)),
 path('auth/login/', LoginView.as_view()),
 path('auth/refresh/', TokenRefreshView.as_view()),
 path('auth/me/', MeView.as_view()),
 path('schema/', SchemaView.as_view()),
 path('dashboard/facturacion/', DashboardFacturacionAPIView.as_view(authentication_classes=[JWTAuthentication])),
 path('dashboard/clientes-servicios/', DashboardClientesServiciosAPIView.as_view(authentication_classes=[JWTAuthentication])),
] + router.urls
