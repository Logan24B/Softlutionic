from django.db import models


class Pago(models.Model):
    Fecha_Pago = models.DateTimeField()
    Monto_Pagado = models.DecimalField(max_digits=18, decimal_places=2)
    EstadoPago = models.BooleanField(default=False)
    MetodoPago = models.BooleanField(default=False)
    FacturaId = models.ForeignKey(
        'factura.Factura',
        on_delete=models.PROTECT,
        related_name='pagos',
        db_column='FacturaId',
    )
    NumeroRecibo = models.IntegerField(unique=True)

    class Meta:
        db_table = 'Pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-Fecha_Pago']

    @property
    def estado_descripcion(self):
        return 'Confirmado' if self.EstadoPago else 'No confirmado'

    @property
    def metodo_descripcion(self):
        return 'Transferencia' if self.MetodoPago else 'Efectivo'

    def __str__(self):
        return f'Recibo {self.NumeroRecibo}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from apps.transaccion.factura.services import sincronizar_estado_factura

        sincronizar_estado_factura(self.FacturaId)

    def delete(self, *args, **kwargs):
        factura = self.FacturaId
        super().delete(*args, **kwargs)

        from apps.transaccion.factura.services import sincronizar_estado_factura

        sincronizar_estado_factura(factura)
