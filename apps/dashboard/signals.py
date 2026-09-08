from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalogos.clientes.models import Cliente
from apps.transaccion.contratos.models import Contrato, TipoContrato
from apps.transaccion.factura.models import DetalleFactura, EstadoFactura, Factura
from apps.transaccion.mora.models import Mora
from apps.transaccion.pagos.models import Pago
from .revision import bump_dashboard_revision


DASHBOARD_MODELS = (
    Cliente,
    Contrato,
    TipoContrato,
    Factura,
    DetalleFactura,
    EstadoFactura,
    Pago,
    Mora,
)


@receiver(post_save, sender=Cliente)
@receiver(post_save, sender=Contrato)
@receiver(post_save, sender=TipoContrato)
@receiver(post_save, sender=Factura)
@receiver(post_save, sender=DetalleFactura)
@receiver(post_save, sender=EstadoFactura)
@receiver(post_save, sender=Pago)
@receiver(post_save, sender=Mora)
@receiver(post_delete, sender=Cliente)
@receiver(post_delete, sender=Contrato)
@receiver(post_delete, sender=TipoContrato)
@receiver(post_delete, sender=Factura)
@receiver(post_delete, sender=DetalleFactura)
@receiver(post_delete, sender=EstadoFactura)
@receiver(post_delete, sender=Pago)
@receiver(post_delete, sender=Mora)
def dashboard_data_changed(sender, **kwargs):
    if sender in DASHBOARD_MODELS:
        bump_dashboard_revision()
