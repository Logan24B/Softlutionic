from collections import OrderedDict
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalogos.clientes.models import Cliente
from apps.transaccion.contratos.models import Contrato
from apps.transaccion.factura.models import DetalleFactura, Factura
from apps.transaccion.mora.models import Mora
from apps.transaccion.pagos.models import Pago
from .revision import get_dashboard_revision


MONEY_FIELD = DecimalField(max_digits=18, decimal_places=2)


class IsDashboardAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.Rol)


class DashboardVersionAPIView(APIView):
    permission_classes = [IsDashboardAdmin]

    def get(self, request):
        return Response({"revision": get_dashboard_revision()})


def money(value):
    return float(value or Decimal("0.00"))


def date_filters(request):
    filters = {}
    start = parse_date(request.query_params.get("start") or "")
    end = parse_date(request.query_params.get("end") or "")
    if start:
        filters["Fecha_Emision__gte"] = start
    if end:
        filters["Fecha_Emision__lte"] = end
    return filters


def invoice_queryset(request):
    return Factura.objects.select_related("ContratoId__ClienteId", "EstadoId").filter(
        **date_filters(request)
    )


class DashboardFacturacionAPIView(APIView):
    permission_classes = [IsDashboardAdmin]

    def get(self, request):
        facturas = invoice_queryset(request)
        factura_ids = facturas.values("id")

        total_facturado = facturas.aggregate(
            total=Coalesce(Sum("Monto_Total"), Value(Decimal("0.00")), output_field=MONEY_FIELD)
        )["total"]
        total_pagado = Pago.objects.filter(FacturaId__in=factura_ids).aggregate(
            total=Coalesce(Sum("Monto_Pagado"), Value(Decimal("0.00")), output_field=MONEY_FIELD)
        )["total"]
        total_mora = Mora.objects.filter(FacturaId__in=factura_ids).aggregate(
            total=Coalesce(Sum("Monto_Mora"), Value(Decimal("0.00")), output_field=MONEY_FIELD)
        )["total"]

        facturado_por_mes = OrderedDict()
        for item in facturas.order_by("Fecha_Emision").values("Fecha_Emision", "Monto_Total"):
            label = item["Fecha_Emision"].strftime("%Y-%m")
            facturado_por_mes[label] = facturado_por_mes.get(label, Decimal("0.00")) + (
                item["Monto_Total"] or Decimal("0.00")
            )

        estados = list(
            facturas.values(label=F("EstadoId__estado"))
            .annotate(value=Count("id"))
            .order_by("EstadoId__estado")
        )

        tabla_facturas = [
            {
                "CodigoFact": factura.CodigoFact,
                "Fecha_Emision": factura.Fecha_Emision.isoformat(),
                "Monto_Total": money(factura.Monto_Total),
                "estado": factura.EstadoId.estado if factura.EstadoId else "Sin estado",
            }
            for factura in facturas.order_by("-Fecha_Emision", "-Hora_Emision")[:12]
        ]

        return Response(
            {
                "cards": {
                    "total_facturado": money(total_facturado),
                    "total_pagado": money(total_pagado),
                    "saldo_pendiente": money(total_facturado - total_pagado),
                    "total_mora": money(total_mora),
                },
                "charts": {
                    "facturado_por_mes": [
                        {"label": label, "value": money(value)}
                        for label, value in facturado_por_mes.items()
                    ],
                    "facturas_por_estado": estados,
                },
                "tables": {"facturas": tabla_facturas},
            }
        )


class DashboardClientesServiciosAPIView(APIView):
    permission_classes = [IsDashboardAdmin]

    def get(self, request):
        facturas = invoice_queryset(request)
        factura_ids = facturas.values("id")

        total_facturado = facturas.aggregate(
            total=Coalesce(Sum("Monto_Total"), Value(Decimal("0.00")), output_field=MONEY_FIELD)
        )["total"]
        cantidad_facturas = facturas.count()
        ticket_promedio = total_facturado / cantidad_facturas if cantidad_facturas else Decimal("0.00")

        line_total = ExpressionWrapper(
            F("PrecioVenta") * F("Cantidad"),
            output_field=MONEY_FIELD,
        )
        ingresos_por_servicio = list(
            DetalleFactura.objects.filter(FacturaId__in=factura_ids)
            .values(label=F("ServicioId__Nombre_Servicio"))
            .annotate(value=Coalesce(Sum(line_total), Value(Decimal("0.00")), output_field=MONEY_FIELD))
            .order_by("-value")[:10]
        )
        total_ingresos_servicio = sum(
            (item["value"] or Decimal("0.00")) for item in ingresos_por_servicio
        )
        contratos_por_tipo = list(
            Contrato.objects.values(label=F("TipoContratoId__Nombre"))
            .annotate(value=Count("id"))
            .order_by("TipoContratoId__Nombre")
        )
        clientes_por_departamento = list(
            Cliente.objects.values(label=F("DepartamentoId__Nombre"))
            .annotate(value=Count("id"))
            .order_by("DepartamentoId__Nombre")
        )

        tabla_comercial = [
            {
                "Nombre": contrato.ClienteId.Nombre,
                "Apellido": contrato.ClienteId.Apellido,
                "Telefono": contrato.ClienteId.Telefono,
                "EstadoContrato": "Activo" if contrato.EstadoContrato else "Finalizado",
                "TipoContrato": contrato.TipoContratoId.Nombre if contrato.TipoContratoId else "Sin tipo",
            }
            for contrato in Contrato.objects.select_related(
                "ClienteId", "TipoContratoId"
            ).order_by("ClienteId__Nombre", "ClienteId__Apellido")[:12]
        ]

        return Response(
            {
                "cards": {
                    "cantidad_clientes": Cliente.objects.count(),
                    "cantidad_contratos": Contrato.objects.count(),
                    "ticket_promedio": money(ticket_promedio),
                    "ingresos_por_servicio": money(total_ingresos_servicio),
                },
                "charts": {
                    "ingresos_por_servicio": [
                        {"label": item["label"] or "Sin servicio", "value": money(item["value"])}
                        for item in ingresos_por_servicio
                    ],
                    "contratos_por_tipo": [
                        {"label": item["label"] or "Sin tipo", "value": item["value"]}
                        for item in contratos_por_tipo
                    ],
                    "clientes_por_departamento": [
                        {"label": item["label"] or "Sin departamento", "value": item["value"]}
                        for item in clientes_por_departamento
                    ],
                },
                "tables": {"comercial": tabla_comercial},
            }
        )

