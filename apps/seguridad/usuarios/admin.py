from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


@admin.register(User)
class SoftFacturUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('SoftFactur', {'fields': ('PrimerNombre', 'SegundoNombre', 'FechaRegistro', 'HoraRegistro', 'Rol')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SoftFactur', {'fields': ('PrimerNombre', 'SegundoNombre', 'Rol', 'email')}),
    )
    list_display = ('id', 'username', 'PrimerNombre', 'SegundoNombre', 'email', 'Rol', 'FechaRegistro', 'HoraRegistro', 'is_active')
    list_filter = UserAdmin.list_filter + ('Rol',)
    search_fields = ('username', 'PrimerNombre', 'SegundoNombre', 'email')
    readonly_fields = ('FechaRegistro', 'HoraRegistro')
