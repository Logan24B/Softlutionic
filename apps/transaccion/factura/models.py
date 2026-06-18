from django.conf import settings
from django.db import models
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from decimal import Decimal


class EstadoFactura(models.Model):
    estado = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'estado_factura'
        verbose_name = 'Estado de factura'
        verbose_name_plural = 'Estados de factura'
        ordering = ['id']

    def __str__(self):
        return self.estado


class Factura(models.Model):
    UsuarioId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='facturas',
        db_column='UsuarioId',
    )
    ContratoId = models.ForeignKey(
        'contratos.Contrato',
        on_delete=models.PROTECT,
        related_name='facturas',
        db_column='ContratoId',
    )
    Fecha_Emision = models.DateField()
    Hora_Emision = models.TimeField()
    Fecha_Vencimiento = models.DateField()
    Hora_Vencimiento = models.TimeField()
    Monto_Total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    CodigoFact = models.IntegerField(unique=True)
    EstadoId = models.ForeignKey(
        EstadoFactura,
        on_delete=models.PROTECT,
        related_name='facturas',
        db_column='EstadoId',
        default=1,
    )

    class Meta:
        db_table = 'Facturas'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-Fecha_Emision']

    def __str__(self):
        return f'Factura {self.CodigoFact}'

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if update_fields is None or {'Fecha_Emision', 'ContratoId'} & set(update_fields):
            from .services import aplicar_vencimiento_por_contrato

            aplicar_vencimiento_por_contrato(self)
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'Fecha_Vencimiento', 'Hora_Vencimiento'}

        super().save(*args, **kwargs)

    def recalcular_total(self):
        total = self.detalles.aggregate(
            total=Coalesce(
                Sum(
                    F('PrecioVenta') * F('Cantidad'),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                ),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )['total']

        self.Monto_Total = total
        Factura.objects.filter(pk=self.pk).update(Monto_Total=total)

        from .services import sincronizar_mora_factura

        sincronizar_mora_factura(self)


class DetalleFactura(models.Model):
    FacturaId = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles',
        db_column='FacturaId',
    )
    ServicioId = models.ForeignKey(
        'servicios.Servicio',
        on_delete=models.PROTECT,
        related_name='detalles_factura',
        db_column='ServicioId',
    )
    PrecioVenta = models.IntegerField()
    Cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'Detalle_Factura'
        verbose_name = 'Detalle de factura'
        verbose_name_plural = 'Detalles de factura'
        ordering = ['id']

    def __str__(self):
        return f'{self.ServicioId} en {self.FacturaId}'

    @property
    def Subtotal(self):
        return self.PrecioVenta * self.Cantidad

    def save(self, *args, **kwargs):
        if self.PrecioVenta is None and self.ServicioId:
            self.PrecioVenta = self.ServicioId.Precio
        super().save(*args, **kwargs)
        self.FacturaId.recalcular_total()

    def delete(self, *args, **kwargs):
        factura = self.FacturaId
        super().delete(*args, **kwargs)
        factura.recalcular_total()
