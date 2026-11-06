"""Reuse the existing business API; no duplicate enterprise models."""
from apps.catalogos.clientes.api import ClienteViewSet
from apps.catalogos.departamentos.api import DepartamentosViewSet
from apps.catalogos.servicios.api import ServicioViewSet
from apps.seguridad.usuarios.api import UserViewSet
from apps.transaccion.contratos.api import ContratoViewSet, TipoContratoViewSet
from apps.transaccion.factura.api import FacturaViewSet, EstadoFacturaViewSet
from apps.transaccion.pagos.api import PagoViewSet
from apps.transaccion.mora.api import MoraViewSet
from apps.transaccion.notificaciones.api import NotificacionViewSet
from apps.transaccion.auditoria.api import LogAuditoriaViewSet
MODULES = {
 'clientes': ClienteViewSet, 'departamentos': DepartamentosViewSet,
 'servicios': ServicioViewSet, 'usuarios': UserViewSet,
 'contratos': ContratoViewSet, 'tipos-contrato': TipoContratoViewSet,
 'facturas': FacturaViewSet, 'estados-factura': EstadoFacturaViewSet,
 'pagos': PagoViewSet, 'moras': MoraViewSet,
 'notificaciones': NotificacionViewSet, 'auditoria': LogAuditoriaViewSet,
}
from .policy import MobileAuthorizationPolicy as Policy

ADMIN_ONLY = {'usuarios', 'auditoria'}
READ_ONLY = {'estados-factura', 'moras', 'auditoria', 'notificaciones'}
def capabilities(user, name):
    read = bool(user.is_authenticated and (name not in ADMIN_ONLY or Policy.is_admin(user)))
    write = read and name not in READ_ONLY
    existing = {'read': read, 'create': write, 'update': write,
                'delete': write and name not in {'facturas', 'pagos'}}
    return {operation: allowed and Policy.allows(user, name, operation)
            for operation, allowed in existing.items()}
