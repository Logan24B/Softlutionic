# Reportes gerenciales

Acceso: menú Reportes, únicamente para usuarios con `Rol=True`. El endpoint
`GET /api/reportes/?start=AAAA-MM-DD&end=AAAA-MM-DD` aplica el mismo permiso.
No requiere migraciones ni modifica facturas, pagos o contratos.

El período predeterminado es el mes actual hasta hoy. Se rechazan fechas inválidas,
futuras, invertidas y rangos superiores a 1095 días.

- Facturación y clientes: fecha de emisión, excluyendo facturas anuladas.
- Servicios: precio de venta por cantidad del detalle, excluyendo anuladas.
- Cobros: fecha del pago confirmado, incluso para facturas emitidas fuera del período.
- Cartera: situación actual; saldo máximo entre cero y total menos pagos confirmados
  hasta el momento de generación. No compensa sobrepagos de otras facturas ni incluye mora.
- Antigüedad: fecha y hora de vencimiento; los atrasos del mismo día cuentan como un día.
- Renovaciones: contratos activos, ya iniciados, que vencen entre hoy y 30 días inclusive.

Los reportes usan córdobas (NIO). CSV incluye todas las filas, período y fecha de
generación; neutraliza celdas que podrían interpretarse como fórmulas.
La impresión incluye todas las filas, aunque la pantalla muestre páginas de 15 registros.

Pruebas: `python manage.py test apps.dashboard.test_reports` utiliza la base de
pruebas del entorno configurado. Las pruebas también pueden ejecutarse con SQLite
en memoria sustituyendo DATABASES antes de django.setup(), sin tocar SQL Server.

La consulta de cartera recorre las facturas y carga sus pagos confirmados en lote.
Para volúmenes muy grandes conviene agregar los saldos en SQL y paginar en servidor;
la implementación actual devuelve el conjunto completo para impresión y exportación.
