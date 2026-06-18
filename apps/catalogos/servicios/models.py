from django.db import models


class Servicio(models.Model):
    Nombre_Servicio = models.CharField(max_length=50, unique=True)
    Descripcion = models.CharField(max_length=200)
    Precio = models.IntegerField()
    Duracion = models.CharField(max_length=50)

    class Meta:
        db_table = 'Servicios'
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['Nombre_Servicio']

    def __str__(self):
        return self.Nombre_Servicio
