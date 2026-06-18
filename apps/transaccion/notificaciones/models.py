from django.db import models


class Notificacion(models.Model):
    ClienteId = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='notificaciones',
        db_column='ClienteId',
    )
    Fecha_Envio = models.DateTimeField()
    Mensaje = models.CharField(max_length=250)
    EstadoNotificacion = models.BooleanField(default=False)

    class Meta:
        db_table = 'Notificaciones'
        verbose_name = 'Notificacion'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-Fecha_Envio']

    @property
    def estado_descripcion(self):
        return 'Leida' if self.EstadoNotificacion else 'No leida'

    def __str__(self):
        return f'Notificacion {self.id} - {self.ClienteId}'

