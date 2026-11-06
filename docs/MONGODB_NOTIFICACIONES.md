# Notificaciones MongoDB para Softlutionic

## Arquitectura inspeccionada

`SoftFactur/settings.py` configura Django 4.2, DRF, usuario personalizado
`usuarios.user`, SQL Server mediante `SoftFactur/database_config.py`, sesiones web
y zona horaria America/Managua. `SoftFactur/urls.py` separa `/api/` (web) de
`/api/mobile/v1/`. Las aplicaciones se agrupan en catálogos, seguridad,
transacciones y dashboard; los routers y serializers reutilizan los modelos SQL.

La API móvil construye ViewSets a partir de `registry.MODULES`, incorpora JWT,
`MobilePermission`, capacidades y `MobileAuthorizationPolicy`. El login acepta
usuario/correo, devuelve access/refresh e identidad; `auth/me/` y `schema/`
describen identidad, permisos y campos. Los módulos existentes son clientes,
departamentos, servicios, usuarios, contratos, tipos-contrato, facturas,
estados-factura, pagos, moras, notificaciones y auditoría, además de dashboard.

`Factura` tiene `CodigoFact`, `UsuarioId`, `ContratoId`, fechas/horas, estado y
total calculado desde `DetalleFactura`. El serializer asigna estado Pendiente;
el modelo aplica vencimiento según contrato. La API móvil usa
`AtomicInvoiceSerializer` con `lineas`, usuario autenticado y transacción en
`MobileMixin.create`: una línea inválida revierte la factura completa.

`Pago` usa `NumeroRecibo`, `FacturaId`, `Monto_Pagado`, `Fecha_Pago`,
`EstadoPago` y `MetodoPago`. Su guardado y serializer sincronizan el estado
de factura y mora. Esa lógica se conserva. `EstadoPago=False` significa pago
no confirmado: también se notifica su registro, sin afirmar que fue confirmado.

El modelo SQL `Notificacion` usa `ClienteId`, `Fecha_Envio`, `Mensaje` y
`EstadoNotificacion`. Su tabla, migraciones, admin y `/api/notificaciones/`
siguen disponibles. Solo la ruta móvil de notificaciones pasa a MongoDB.
No se mezclan ni migran registros SQL hacia MongoDB.

## Implementación

- `apps/transaccion/notificaciones/mongo.py`: cliente lazy reutilizado por
  proceso, pool de PyMongo, acceso compartido y publicación tras commit.
- `apps/mobile_api/notifications.py`: ViewSet JWT, filtro por rol, serialización
  explícita y lecturas individuales. SUPERUSER depende de `is_superuser`;
  ADMIN de `Rol` sin superusuario; EMPLOYEE es el resto. `is_staff` no decide.
- Serializers compartidos de factura y pago: creación SQL atómica y callback
  `transaction.on_commit`. La transacción exterior móvil mantiene pendiente el
  callback hasta terminar las líneas. Las actualizaciones no generan otro evento.
- `registry.py`, `api.py`, `urls.py`: registro móvil y schema sin formulario CRUD
  SQL para notificaciones. `update=false` en capacidades se refiere al CRUD
  genérico; la acción específica `/leer/` está disponible para usuarios autenticados.

No se emplean señales: disparar `post_save` desde `Pago.save` en autocommit
podría publicar antes de terminar su sincronización de factura. Los puntos de
integración elegidos cubren las API web y móvil, que usan estos serializers.
Creaciones directas por ORM, bulk_create, scripts o Django admin no generan
estos eventos; deberán pasar por una capa transaccional explícita si se amplía
ese alcance.

## Configuración

Dependencia: `pymongo>=4.19,<5.0` en `requirements.txt` (driver oficial; incluye
dnspython como dependencia para Atlas SRV). No se añade ODM ni backend Django MongoDB.

Variables:

| Variable | Valor |
| --- | --- |
| `MONGODB_URI` | Obligatoria para operar Mongo; configurar secretamente en el entorno |
| `MONGODB_DATABASE` | Opcional: `softlutionic_nosql` |
| `MONGODB_NOTIFICATIONS_COLLECTION` | Opcional: `notificaciones` |

No guardar la URI en Git ni en comandos compartidos. Configurar usuario Atlas
con acceso a la base y lista de acceso de red para el servidor Django.
Reiniciar procesos Django después de modificar la configuración. No se conecta
durante el arranque. Sin URI, Django inicia; las consultas Mongo responden 503
y los eventos SQL confirmados registran error de publicación.

## Endpoints y ejemplos

Todos requieren `Authorization: Bearer <access JWT>`:

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/api/mobile/v1/notificaciones/` | Array visible, fecha descendente |
| GET | `/api/mobile/v1/notificaciones/no-leidas/count/` | `{"count": 3}` |
| PATCH | `/api/mobile/v1/notificaciones/{mongo_id}/leer/` | Documento con `leida: true` |

Ejemplo ilustrativo de listado:

```json
[
  {
    "id": "690c1c000000000000000001",
    "tipo": "factura_generada",
    "titulo": "Nueva factura generada",
    "mensaje": "Se registró la factura 123.",
    "origen": "django_softlutionic",
    "prioridad": "normal",
    "estado": "activa",
    "fecha_creacion": "2026-11-06T06:17:27.307000Z",
    "leida": false,
    "referencia": {"tipo": "factura", "id_sql": 12, "codigo_factura": 123}
  }
]
```

El PATCH usa cuerpo `{}` y devuelve el mismo documento con `leida: true`.
No expone las lecturas de otros usuarios. Los campos de identidad o rol que
envíe el cliente no participan en permisos ni lecturas. El filtro de actualización
incluye rol, `_id` y `lecturas.usuario_id_sql: {$ne: request.user.pk}` con `$push`;
la condición se evalúa atómicamente y evita duplicados por usuario.
Un ID inválido, inexistente o invisible devuelve 404. Sin autenticación: 401.
Mongo no disponible: 503 con detalle genérico. No se filtra adicionalmente por
estado: el requisito de visibilidad se basa en destinatarios_roles.

## Prueba local

Usar base SQL y base/colección Mongo de desarrollo, nunca datos productivos
para pruebas de escritura. Configurar las variables del backend y Mongo en la
terminal local o gestor de secretos. En un entorno virtual:

```powershell
python -m pip install -r requirements.txt
$env:SOFTFACTUR_DEBUG = 'true'
python manage.py runserver
```

Autenticar con una cuenta de desarrollo, obteniendo `access` desde
`POST /api/mobile/v1/auth/login/` con `username` y `password`. Luego:

```powershell
$headers = @{ Authorization = "Bearer $access" }
$base = 'http://127.0.0.1:8000/api/mobile/v1/notificaciones/'
$items = Invoke-RestMethod -Uri $base -Headers $headers
Invoke-RestMethod -Uri ($base + 'no-leidas/count/') -Headers $headers
Invoke-RestMethod -Method Patch -Uri ($base + $items[0].id + '/leer/') -Headers $headers -ContentType 'application/json' -Body '{}'
```

Repetir PATCH y verificar que el conteo permanece igual. Con otra cuenta la
lectura debe seguir pendiente. EMPLOYEE no debe recibir documentos exclusivos
de ADMIN/SUPERUSER. Android solo necesita Django y su JWT; no recibe URI Atlas.

Crear una factura/pago con el flujo normal en desarrollo. En Atlas Data Explorer,
seleccionar la base configurada y `notificaciones`; filtrar:

```json
{"origen": "django_softlutionic", "tipo": "factura_generada"}
```

Ordenar por `fecha_creacion: -1`; comprobar `referencia.id_sql` y
`referencia.codigo_factura` contra `Factura.id` y `CodigoFact`. Para pagos,
filtrar `tipo: "pago_registrado"` y verificar `id_sql`, `factura_id_sql`.
Después del PATCH revisar `lecturas`: una entrada con el ID SQL autenticado y
fecha UTC, aunque se repita la petición. No modificar índices de producción
automáticamente; si crece el volumen evaluar un índice compuesto en
`destinatarios_roles`, `fecha_creacion` y `_id`.

## Pruebas automáticas y límites

```powershell
python manage.py test apps.mobile_api apps.transaccion.factura --settings=apps.mobile_api.test_settings --noinput -v 1
python manage.py check --settings=apps.mobile_api.test_settings
git diff --check
```

SQL se sustituye por SQLite en memoria. Mongo se sustituye por mocks y un fake
de consultas: no hay escrituras ni conexiones a Azure/Atlas. Las pruebas cubren
roles, is_staff, conteos, serialización, lectura repetida y por usuario, acceso
invisible/anónimo, orden, error 503, commit/rollback, líneas móviles inválidas y
persistencia SQL tras fallo Mongo. La concurrencia real y compatibilidad del
servidor Atlas requieren validación adicional en desarrollo; el test del PATCH
comprueba el filtro y operador atómicos, no simula un servidor Mongo concurrente.

No existe transacción distribuida ni reintento persistente. Si Mongo falla o el
proceso muere después del commit SQL, puede faltar una notificación; SQL sigue
confirmado. Se registra tipo, ID SQL y clase de error sin URI ni texto sensible.
No se garantiza entrega exactamente una vez. El callback es síncrono, con
presupuesto de operación de 5 segundos y timeouts de conexión/socket de 3.
El listado conserva la convención móvil de array sin paginar; evaluar paginación
si crece el historial. El contrato JSON móvil cambia respecto a SQL: el cliente
Android existente necesitará adaptación a ID string, campos y acción `/leer/`.

No se agregan migraciones SQL, no se modifica Android, y no se hace commit/push.

Validación ejecutada: 38 pruebas correctas (26 existentes y 12 nuevas),
`manage.py check` sin incidencias y `git diff --check` correcto. Aviso no bloqueante:
falta el directorio de estáticos recopilados. Se probaron PyMongo 4.19.0 y
dnspython 2.9.2 instalados dentro de `.runtime/mongo-deps` (ignorado por Git),
porque la instalación global no tenía permisos. Para repetir en este mismo
entorno, establecer `$env:PYTHONPATH = "$PWD\.runtime\mongo-deps"` antes de los
comandos de prueba. No se verificó conexión real a Atlas ni Azure.
