from django.db import models

class Cliente(models.Model):
    Nombre1 = models.CharField(max_length=30)
    Nombre2 = models.CharField(max_length=30, blank=True, null=True)  # opcional si quieres
    Apellido1 = models.CharField(max_length=30)
    Apellido2 = models.CharField(max_length=30, blank=True, null=True)  # opcional
    Email = models.EmailField(max_length=100, unique=True)
    Estado = models.BooleanField(default=True)
    Celular = models.CharField(max_length=30)
    Direccion = models.CharField(max_length=100)
    Fecha = models.DateField()  # si es fecha de registro podrías usar auto_now_add=True

    class Meta:
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.Nombre1} {self.Apellido1} - {self.Email}"


# Create your models here.
