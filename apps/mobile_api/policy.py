"""Hierarchy restrictions applied only to the mobile API."""
from rest_framework.exceptions import PermissionDenied


class MobileAuthorizationPolicy:
    EMPLOYEE_READ_ONLY_MODULES = frozenset({'servicios', 'tipos-contrato'})

    @staticmethod
    def role(user):
        if user.is_superuser:
            return 'Superusuario'
        return 'Administrador' if user.Rol else 'Empleado'

    @staticmethod
    def is_admin(user):
        return bool(user.is_superuser or user.Rol)

    @classmethod
    def allows(cls, user, module, operation):
        if module == 'usuarios':
            return cls.is_admin(user)
        if module in cls.EMPLOYEE_READ_ONLY_MODULES and operation != 'read':
            return cls.is_admin(user)
        return True

    @staticmethod
    def visible_users(actor, queryset):
        """Collections expose all accounts to superusers and employees to admins."""
        if actor.is_superuser:
            return queryset
        if actor.Rol:
            return queryset.filter(is_superuser=False, Rol=False)
        return queryset.none()

    @classmethod
    def check_user_access(cls, actor, target, read_only=False):
        """Existing forbidden detail resources consistently return HTTP 403."""
        if read_only:
            if actor.is_superuser:
                return
            if not actor.Rol or target.is_superuser or target.Rol:
                raise PermissionDenied('No tienes permiso para consultar esta cuenta de usuario.')
            return
        cls.check_target(actor, target)

    @staticmethod
    def check_target(actor, target):
        # Superuser accounts are managed through backend administration only.
        if target.is_superuser:
            raise PermissionDenied('Las cuentas de superusuario se administran desde Django.')
        if not actor.is_superuser and target.Rol:
            raise PermissionDenied('Solo el superusuario puede administrar cuentas administrativas.')

    @staticmethod
    def check_payload(actor, data, creating=False):
        if {'is_superuser', 'is_staff'}.intersection(data):
            raise PermissionDenied('is_superuser e is_staff son de solo lectura en la API móvil.')
        if data.get('Rol') and not actor.is_superuser:
            message = ('Solo el superusuario puede crear cuentas administrativas.' if creating
                       else 'Solo el superusuario puede asignar el rol Administrador.')
            raise PermissionDenied(message)
