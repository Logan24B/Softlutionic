from urllib.parse import urlparse

from django.http import HttpResponse


class DevCorsMiddleware:
    """Permite consumir la API desde el frontend local durante la defensa."""

    allowed_hosts = {'127.0.0.1', 'localhost', '::1'}

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_allowed_origin(self, origin):
        if not origin:
            return False
        if origin == 'null':
            return True

        parsed = urlparse(origin)
        return parsed.scheme in {'http', 'https'} and parsed.hostname in self.allowed_hosts

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        origin = request.headers.get('Origin')
        if self._is_allowed_origin(origin):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                request.headers.get(
                    'Access-Control-Request-Headers',
                    'Content-Type, Authorization, X-Requested-With, X-CSRFToken',
                )
            )
            response['Access-Control-Max-Age'] = '600'
            response['Vary'] = 'Origin'
        return response
