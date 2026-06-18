from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.conf import settings


def serve_frontend(request, path):
    response = serve(request, path, document_root=settings.BASE_DIR / 'frontend')
    if path.lower().endswith('.html'):
        response['Content-Type'] = 'text/html; charset=utf-8'
        response['Cache-Control'] = 'no-store, max-age=0'
    return response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('factura-demo/', TemplateView.as_view(template_name='factura_demo.html'), name='factura_demo'),
    path('', RedirectView.as_view(url='/frontend/Softlutionic/login.html', permanent=False)),
    path('frontend/', RedirectView.as_view(url='/frontend/Softlutionic/login.html', permanent=False)),
    path('frontend/<path:path>', serve_frontend),
    path('api/', include('apps.urls')),
]
