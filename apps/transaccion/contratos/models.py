from django.db import models


class TipoContrato(models.Model):
    Nombre = models.CharField(max_length=80, unique=True)
    Descripcion = models.CharField(max_length=250, blank=True)

    class Meta:
        db_table = 'TipoContrato'
        verbose_name = 'Tipo de contrato'
        verbose_name_plural = 'Tipos de contrato'
        ordering = ['Nombre']

    def __str__(self):
        return self.Nombre


class Contrato(models.Model):
    ClienteId = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='contratos',
        db_column='ClienteId',
    )
    TipoContratoId = models.ForeignKey(
        TipoContrato,
        on_delete=models.PROTECT,
        related_name='contratos',
        db_column='TipoContratoId',
        null=True,
        blank=True,
    )
    Fecha_Inc = models.DateField()
    Fecha_Fin = models.DateField()
    EstadoContrato = models.BooleanField(default=True)
    Descripcion = models.CharField(max_length=250)

    class Meta:
        db_table = 'Contratos'
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-Fecha_Inc']

    def __str__(self):
        return f'Contrato {self.id} - {self.ClienteId}'
