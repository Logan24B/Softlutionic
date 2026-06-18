from django.urls import include, path

urlpatterns = [
    path('', include('apps.catalogos.clientes.urls')),
    path('', include('apps.catalogos.departamentos.urls')),
    path('', include('apps.catalogos.servicios.urls')),
    path('', include('apps.seguridad.usuarios.urls')),
    path('', include('apps.transaccion.contratos.urls')),
    path('', include('apps.transaccion.factura.urls')),
    path('', include('apps.transaccion.pagos.urls')),
    path('', include('apps.transaccion.mora.urls')),
    path('', include('apps.transaccion.notificaciones.urls')),
    path('', include('apps.transaccion.auditoria.urls')),
]
