from django.db import models


class Mora(models.Model):
    Fecha_Inicio = models.DateField()
    Hora_Inicio = models.TimeField()
    Fecha_Final = models.DateField()
    Hora_Final = models.TimeField()
    Monto_Mora = models.DecimalField(max_digits=18, decimal_places=2)
    EstadoMora = models.BooleanField(default=False)
    FacturaId = models.OneToOneField(
        'factura.Factura',
        on_delete=models.PROTECT,
        related_name='mora',
        db_column='FacturaId',
    )
    DescripcionMora = models.CharField(max_length=500)

    class Meta:
        db_table = 'Mora'
        verbose_name = 'Mora'
        verbose_name_plural = 'Moras'
        ordering = ['-Fecha_Inicio', '-Hora_Inicio']

    def __str__(self):
        return f'Mora {self.id} - {self.FacturaId}'

    @property
    def estado_descripcion(self):
        return 'Pagada' if self.EstadoMora else 'Pendiente'
