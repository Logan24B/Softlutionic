from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone


ESTADO_PENDIENTE = 'Pendiente'
ESTADO_PAGADA = 'Pagada'
ESTADO_VENCIDA = 'Vencida'
ESTADO_ANULADA = 'Anulada'
TIPO_CONTRATO_MENSUAL = 'Servicio mensual'
HORA_FIN_DIA = time(23, 59, 0)
PORCENTAJE_MORA_DIARIA = Decimal('0.0007')


def es_contrato_mensual(factura):
    tipo = getattr(getattr(factura.ContratoId, 'TipoContratoId', None), 'Nombre', '')
    return tipo.strip().lower() == TIPO_CONTRATO_MENSUAL.lower()


def calcular_vencimiento(fecha_emision, contrato):
    tipo = getattr(getattr(contrato, 'TipoContratoId', None), 'Nombre', '')
    dias_plazo = 30 if tipo.strip().lower() == TIPO_CONTRATO_MENSUAL.lower() else 0
    return fecha_emision + timedelta(days=dias_plazo), HORA_FIN_DIA


def factura_pagada(factura):
    return factura.pagos.filter(EstadoPago=True).exists()


def fecha_pago_confirmado(factura):
    pago = factura.pagos.filter(EstadoPago=True).order_by('Fecha_Pago').first()
    if not pago:
        return None

    return timezone.localtime(pago.Fecha_Pago)


def fecha_hora_vencimiento(factura):
    vencimiento = datetime.combine(factura.Fecha_Vencimiento, factura.Hora_Vencimiento)
    return timezone.make_aware(vencimiento, timezone.get_current_timezone())


def factura_vencida(factura, ahora=None):
    ahora = ahora or timezone.localtime()
    return ahora > fecha_hora_vencimiento(factura)


def dias_en_mora(factura, fecha_final=None):
    fecha_final = fecha_final or timezone.localtime()

    if fecha_final <= fecha_hora_vencimiento(factura):
        return 0

    return max(1, (fecha_final.date() - factura.Fecha_Vencimiento).days)


def calcular_monto_mora(factura, fecha_final=None):
    monto = Decimal(factura.Monto_Total or 0) * PORCENTAJE_MORA_DIARIA * dias_en_mora(factura, fecha_final)
    return monto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def obtener_estado(nombre):
    from .models import EstadoFactura

    return EstadoFactura.objects.get(estado__iexact=nombre)


def aplicar_vencimiento_por_contrato(factura):
    if not factura.Fecha_Emision or not factura.ContratoId_id:
        return factura

    factura.Fecha_Vencimiento, factura.Hora_Vencimiento = calcular_vencimiento(
        factura.Fecha_Emision,
        factura.ContratoId,
    )
    return factura


def sincronizar_estado_factura(factura, ahora=None, guardar=True):
    estado_actual = getattr(getattr(factura, 'EstadoId', None), 'estado', '')
    if estado_actual.lower() == ESTADO_ANULADA.lower():
        return factura

    if factura_pagada(factura):
        nuevo_estado = obtener_estado(ESTADO_PAGADA)
    elif factura_vencida(factura, ahora):
        nuevo_estado = obtener_estado(ESTADO_VENCIDA)
    else:
        nuevo_estado = obtener_estado(ESTADO_PENDIENTE)

    if factura.EstadoId_id != nuevo_estado.id:
        factura.EstadoId = nuevo_estado
        if guardar:
            factura.save(update_fields=['EstadoId'])

    if guardar:
        sincronizar_mora_factura(factura, ahora)

    return factura


def sincronizar_mora_factura(factura, ahora=None):
    from apps.transaccion.mora.models import Mora

    ahora = ahora or timezone.localtime()
    fecha_pago = fecha_pago_confirmado(factura)
    fecha_final_mora = fecha_pago or ahora
    mora_pagada = fecha_pago is not None
    debe_tener_mora = es_contrato_mensual(factura) and dias_en_mora(factura, fecha_final_mora) > 0

    if not debe_tener_mora:
        Mora.objects.filter(FacturaId=factura).delete()
        return None

    inicio = fecha_hora_vencimiento(factura)
    dias = dias_en_mora(factura, fecha_final_mora)
    monto = calcular_monto_mora(factura, fecha_final_mora)

    mora, _ = Mora.objects.update_or_create(
        FacturaId=factura,
        defaults={
            'Fecha_Inicio': inicio.date(),
            'Hora_Inicio': inicio.time().replace(microsecond=0),
            'Fecha_Final': fecha_final_mora.date(),
            'Hora_Final': fecha_final_mora.time().replace(microsecond=0),
            'Monto_Mora': monto,
            'EstadoMora': mora_pagada,
            'DescripcionMora': (
                f'Mora generada automaticamente: {dias} dia(s) de atraso '
                f'al {PORCENTAJE_MORA_DIARIA * Decimal("100")}% diario.'
            ),
        },
    )
    return mora


def sincronizar_facturas_vencidas():
    from .models import Factura

    facturas = (
        Factura.objects
        .select_related('EstadoId', 'ContratoId', 'ContratoId__TipoContratoId')
        .prefetch_related('pagos')
        .all()
    )

    for factura in facturas:
        sincronizar_estado_factura(factura)
