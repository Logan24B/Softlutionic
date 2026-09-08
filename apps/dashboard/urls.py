from django.urls import path

from .api import (
    DashboardClientesServiciosAPIView,
    DashboardFacturacionAPIView,
    DashboardVersionAPIView,
)


urlpatterns = [
    path("dashboard/version/", DashboardVersionAPIView.as_view(), name="dashboard_version"),
    path("dashboard/facturacion/", DashboardFacturacionAPIView.as_view(), name="dashboard_facturacion"),
    path(
        "dashboard/clientes-servicios/",
        DashboardClientesServiciosAPIView.as_view(),
        name="dashboard_clientes_servicios",
    ),
]