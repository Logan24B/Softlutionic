from rest_framework.routers import DefaultRouter
from .api import DetalleFacturaViewSet, EstadoFacturaViewSet, FacturaViewSet

router = DefaultRouter()
router.register(r'estados-factura', EstadoFacturaViewSet, basename='estados-factura')
router.register(r'facturas', FacturaViewSet, basename='facturas')
router.register(r'detalles-factura', DetalleFacturaViewSet, basename='detalles-factura')

app_name = 'factura'

urlpatterns = router.urls
