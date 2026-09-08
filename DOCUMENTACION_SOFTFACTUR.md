# Documentación de SoftFactur

## 1. Resumen del proyecto
SoftFactur es una aplicación Django para la gestión de facturación, clientes, contratos, pagos, mora, notificaciones y auditoría. Incluye una API REST construida con Django REST Framework y una interfaz frontend estática ubicada en `frontend/Softlutionic`.

## 2. Tecnologías principales
- Python 3 / Django 4.2
- Django REST Framework 3.14+
- Base de datos SQL Server usando `mssql-django` con un backend personalizado (`SoftFactur.db.backends.mssql_no_mars`)
- Frontend estático servido por Django con HTML, CSS y JS en `frontend/Softlutionic`

## 3. Estructura del repositorio
- `manage.py`: entrada principal para comandos de Django.
- `SoftFactur/`: configuración del proyecto Django.
  - `settings.py`: configuración global.
  - `urls.py`: rutas principales, sirve frontend y API.
  - `cors.py`: middleware CORS de desarrollo.
- `apps/`: aplicaciones Django locales.
  - `catalogos/`: datos maestros (`clientes`, `departamentos`, `servicios`).
  - `seguridad/`: gestión de usuarios y autenticación.
  - `transaccion/`: facturación y transacciones.
- `frontend/`: frontend estático.
- `templates/`: plantillas Django usadas por rutas como `factura_demo.html`.
- `static/`: archivos estáticos adicionales.
- `requirements.txt`: dependencias del proyecto.

## 4. Configuración principal
### `SoftFactur/settings.py`
- `DEBUG = True`
- `SECRET_KEY` está en el repositorio (debe protegerse en producción).
- `ALLOWED_HOSTS = []`
- Apps instaladas:
  - `django.contrib.*`
  - `rest_framework`
  - apps locales agrupadas en:
    - `SEGURIDAD_SETTING_APPS`
    - `CATALOGOS_SETTING_APPS`
    - `TRANSACCION_SETTING_APPS`
- Middleware incluye `SoftFactur.cors.DevCorsMiddleware` para permitir CORS desde `localhost` y `127.0.0.1`.
- `AUTH_USER_MODEL = 'usuarios.user'`.
- REST framework usa autenticación de sesión y básica, y requiere autenticación por defecto.
- Sesiones se manejan en caché local (`LocMemCache`) con expiración en 15 minutos.
- Email configurado por entorno con valores por defecto para Gmail SMTP.

## 5. Base de datos
### `DATABASES`
- `ENGINE`: `SoftFactur.db.backends.mssql_no_mars`
- SQL Server local en `localhost:1433`
- Base: `BDsofactur`
- Driver ODBC: `ODBC Driver 18 for SQL Server`
- Autenticación confiable de Windows (`trusted_connection=yes`)
- `Encrypt=no` y `TrustServerCertificate=yes` para desarrollo local.

## 6. Aplicaciones Django y responsabilidades
### `apps.catalogos`
- `clientes`: CRUD de clientes.
- `departamentos`: CRUD de departamentos.
- `servicios`: CRUD de servicios.

### `apps.seguridad`
- `usuarios`: modelo de usuario extendido, login, sesión, logout y recuperación de contraseña.

### `apps.transaccion`
- `contratos`: tipos de contrato y contratos.
- `factura`: facturas, detalles de factura y estados.
- `pagos`: pagos asociados a facturas.
- `mora`: cálculo y registro de mora.
- `notificaciones`: notificaciones para clientes.
- `auditoria`: logs de auditoría.

## 7. Endpoints principales
### Rutas de frontend y redirecciones
- `/` → redirige a `/frontend/Softlutionic/login.html`
- `/frontend/` → redirige a `/frontend/Softlutionic/login.html`
- `/frontend/<path:path>` → sirve archivos estáticos desde `frontend/`
- `/factura-demo/` → plantilla `factura_demo.html`

### API principal
- `/api/` incluye todas las rutas de aplicaciones locales.

### Seguridad / autenticación
- `/api/auth/login/` POST: login de usuario.
- `/api/auth/session/` GET: devuelve datos de sesión autenticada.
- `/api/auth/logout/` POST: cierra sesión.
- `/api/auth/password-reset/` POST: solicita enlace de recuperación.
- `/api/auth/password-reset/confirm/` POST: confirma cambio de contraseña.
- `/api/usuarios/` CRUD de usuarios.
- `/api/usuarios/administradores/` GET: lista administradores.
- `/api/usuarios/empleados/` GET: lista empleados.

### Catálogos
- `/api/clientes/` CRUD de clientes.
- `/api/departamentos/` CRUD de departamentos.
- `/api/servicios/` CRUD de servicios.

### Transacciones
- `/api/tipos-contrato/` CRUD de tipos de contrato.
- `/api/contratos/` CRUD de contratos.
- `/api/facturas/` CRUD de facturas.
- `/api/detalles-factura/` CRUD de detalles de factura.
- `/api/pagos/` CRUD de pagos.
- `/api/moras/` CRUD de mora.
- `/api/notificaciones/` CRUD de notificaciones.
- `/api/auditoria/` solo lectura de logs de auditoría.

## 8. Modelos clave y relaciones
### Seguridad
- `user`: extiende `AbstractUser` con campos `PrimerNombre`, `SegundoNombre`, `Rol` (booleano), `FechaRegistro`, `HoraRegistro`.
- Se sincronizan `first_name` y `last_name` en `save()`.

### Catálogos
- `Cliente`: vinculado a `Departamento`; campos de contacto, cédula, teléfono, correo y estado.
- `Departamentos`: nombre único.
- `Servicio`: nombre, descripción, precio y duración.

### Contratos y facturas
- `TipoContrato`: nombre y descripción.
- `Contrato`: cliente, tipo de contrato, fechas de inicio/fin, estado y descripción.
- `EstadoFactura`: lista de estados de factura.
- `Factura`: usuario, contrato, fechas y horas de emisión y vencimiento, monto total, código único, estado.
- `DetalleFactura`: servicio, precio de venta, cantidad y subtotal.
- `Pago`: fecha, monto, estado de pago, método, factura asociada y número de recibo.
- `Mora`: mora por factura mensual, fechas, monto, estado y descripción.
- `Notificacion`: mensaje enviado al cliente, estado leído/no leído.
- `LogAuditoria`: auditoría de tabla, acción, usuario, host, fecha y detalle.

## 9. Lógica de negocio importante
### Facturación
- `Factura.save()` calcula vencimiento en función del contrato usando `aplicar_vencimiento_por_contrato()`.
- `Factura.recalcular_total()` suma los detalles y sincroniza la mora.
- Al crear o actualizar una factura se ejecuta `sincronizar_estado_factura()`.

### Mora
- `sincronizar_mora_factura()` crea o elimina el registro de mora según contrato mensual y días de atraso.
- La mora se calcula con una tasa diaria de `0.07%` (`PORCENTAJE_MORA_DIARIA = 0.0007`).

### Pagos
- Guardar o borrar un pago actualiza el estado de la factura asociada.
- Un pago confirmado mueve la factura a estado `Pagada`.

### Contratos
- Los contratos pueden filtrarse por cliente, tipo y estado activo.
- Los tipos de contrato influyen en el cálculo de vencimiento de la factura.

### Validaciones
- Teléfono y cédula de cliente validan formato nicaragüense.
- `Servicio.Precio` no puede ser negativo.
- `Contrato.Fecha_Fin` no puede ser anterior a `Fecha_Inc`.
- `Factura` valida que la fecha/hora de vencimiento no sea anterior a la de emisión.

## 10. Configuración del frontend
- Frontend en `frontend/Softlutionic`.
- La página principal de login es `frontend/Softlutionic/login.html`.
- El frontend se sirve directamente desde Django usando `serve_frontend()` en `SoftFactur/urls.py`.

## 11. Ejecutar el proyecto
1. Crear entorno virtual en Python.
2. Instalar dependencias: `pip install -r requirements.txt`.
3. Configurar conexión a SQL Server según `DATABASES`.
4. Ejecutar migraciones si es necesario: `python manage.py migrate`.
5. Iniciar servidor de desarrollo: `python manage.py runserver`.

## 12. Notas adicionales
- `DEBUG` está activado; no usar en producción.
- `SECRET_KEY` se guarda en código: moverlo a variable de entorno para producción.
- El middleware CORS es específico de desarrollo y solo permite orígenes locales.
- El sistema de email usa variables de entorno para credenciales y configuración SMTP.
- El modelo de usuario personalizado requiere `AUTH_USER_MODEL` y puede afectar migraciones.
- La API REST está protegida por defecto con autenticación y solo permite acceso autenticado salvo endpoints de login y recuperación de contraseña.

---

> Este documento está basado en el código fuente disponible y en la configuración actual del proyecto. Para detalles de implementación de cada módulo, revise los archivos dentro de `apps/`.
