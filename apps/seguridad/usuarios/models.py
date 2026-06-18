from django.contrib.auth.models import AbstractUser
from django.db import models


class user(AbstractUser):
    PrimerNombre = models.CharField(max_length=50)
    SegundoNombre = models.CharField(max_length=50)
    FechaRegistro = models.DateField(auto_now_add=True)
    HoraRegistro = models.TimeField(auto_now_add=True)
    Rol = models.BooleanField(default=False)

    class Meta:
        db_table = 'Usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['PrimerNombre', 'SegundoNombre', 'email']

    @property
    def rol_descripcion(self):
        return 'Administrador' if self.Rol else 'Empleado'

    def save(self, *args, **kwargs):
        if self.PrimerNombre:
            self.first_name = self.PrimerNombre
        if self.SegundoNombre:
            self.last_name = self.SegundoNombre
        self.is_staff = self.Rol
        super().save(*args, **kwargs)

    def __str__(self):
        nombre_completo = f'{self.PrimerNombre} {self.SegundoNombre}'.strip()
        return nombre_completo or self.username or self.email
