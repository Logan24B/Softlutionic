# Ejecucion local de Softlutionic

Estado activo: SQL local como unica base principal. Azure queda pospuesto por solicitud del usuario. Esta guia sustituye el procedimiento anterior; su borrador se conserva en `docs/archive/RECUPERACION_AZURE_BORRADOR.md` solo como referencia historica.

## Configuracion actual

- Proyecto: `C:\Users\softadmin\Desktop\Softlutionic`.
- SQL Server: `localhost\SQLEXPRESS`, base existente `BDsofactur`.
- Autenticacion Windows con la identidad que ejecuta Python; no requiere contrasena SQL.
- Backend: `SoftFactur.db.backends.mssql_no_mars`, mssql-django y ODBC Driver 18.
- Conexion local cifrada con certificado local confiado y timeout de 30 segundos.
- `SoftFactur/database_config.py` devuelve exclusivamente esta conexion. Las antiguas variables SOFTFACTUR_DB_MODE y SOFTFACTUR_PRIVATE_CONFIG ya no seleccionan Azure ni otra base.
- Azure no se consulta al iniciar. Los scripts de Azure se conservan con un bloqueo explicito y su tarea `Softlutionic-AzureToLocal-Daily` esta deshabilitada. No reactivarla: ahora BDsofactur contiene los movimientos principales y una copia desde Azure podria sustituirlos.
- `.private/azure.json` permanece privado e ignorado por Git, pero la aplicacion no lo lee. No copiarlo a otros equipos.

No se crearon, restauraron ni migraron bases para este cambio. Se conserva el contenido existente de BDsofactur. Las operaciones de los usuarios a partir de ahora se registraran alli.

## Iniciar y detener

Desde PowerShell en el proyecto:

```powershell
.\scripts\Start-System.ps1 -Background
```

Para preparar tambien la regla de firewall (requiere permisos de administrador):

```powershell
.\scripts\Start-System.ps1 -Background -OpenFirewall
```

Para ejecutarlo en primer plano, omitir `-Background`; mantener esa consola abierta y detener con Ctrl+C. El script usa Waitress sobre Windows, un solo proceso con cuatro hilos, genera una clave Django persistente privada, comprueba SQL y Django, prepara archivos estaticos con WhiteNoise e inicia en `0.0.0.0:8000`. No ejecuta migraciones. Si el puerto esta ocupado, se detiene sin finalizar procesos ajenos.

Para detener el servidor iniciado en segundo plano:

```powershell
.\scripts\Stop-System.ps1
```

La detencion valida que el PID corresponde al script de este proyecto. No detiene SQL Server. Antes de detener o reiniciar, coordinar con los usuarios para evitar interrumpir solicitudes activas. No hay servicio ni inicio automatico tras reiniciar Windows; ejecutar nuevamente Start-System.ps1. Las sesiones existentes usan cache en memoria y se pierden al reiniciar el proceso: los usuarios vuelven a iniciar sesion.

## Acceso desde la red

Direccion verificada en este servidor el 16 de octubre de 2026:

- Equipo servidor: `http://localhost:8000/`.
- Otros equipos de la misma red: `http://172.16.0.5:8000/`.

Abrir esa URL en el navegador; no abrir login.html directamente, ni ejecutar otro servidor de frontend. Las paginas y la API usan el mismo origen, de modo que cada cliente se conecta al servidor y nunca a su propio localhost. Solo el servidor necesita Python y SQL Server. No se abrio SQL Server a otros equipos.

Regla de firewall creada: `Softlutionic-LAN-8000`, entrada TCP 8000, perfil Private, origen LocalSubnet. El perfil actual de Ethernet es Private. No se cambiaron el perfil ni las reglas generales del sistema. Si los clientes estan en otra subred/VLAN, debe revisarse su ruta y el alcance de esta regla antes de ampliarlo.

Si cambia la IP del servidor, reiniciar con Start-System.ps1 para que agregue la nueva IP a ALLOWED_HOSTS, y comunicar la nueva URL. Es conveniente reservar la IP en DHCP. Para usar un alias DNS adicional, establecer SOFTFACTUR_ALLOWED_HOSTS con nombres separados por coma antes de iniciar. No usar comodines. DEBUG queda desactivado por defecto; no hace falta CORS entre frontend y API.

## Entorno, archivos privados y resultados

Entorno preparado: `.venv`, Python 3.11.17; dependencias declaradas en requirements.txt, incluidas Waitress y WhiteNoise. Para reconstruirlo en este servidor:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

No recrear el entorno mientras el servidor este en uso. La cuenta ejecutora debe tener acceso a BDsofactur mediante autenticacion Windows y permisos sobre el proyecto. No se concedieron nuevos privilegios SQL.

- `.private/django-secret.key`: clave de firma persistente generada al primer arranque; ACL para la cuenta actual y SYSTEM. No versionar, compartir ni regenerar en cada arranque.
- `.runtime/server.json`: PID, puerto, URLs y fecha UTC del ultimo arranque en segundo plano.
- `.runtime/server.out.log` y `.runtime/server.err.log`: salida y errores del servidor. El arranque siguiente reutiliza estos nombres; archivarlos antes si se necesita historial.
- `.runtime/staticfiles`: recursos generados por collectstatic para WhiteNoise.
- `.private/`, `.runtime/`, `.recovery/` y `.tools/`: ignorados por Git.

```powershell
Get-Content .\.runtime\server.json
Get-Content .\.runtime\server.err.log -Tail 30
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\check_database.py
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

## Verificacion realizada y limites

- Conexion real Django/ODBC a BDsofactur exitosa.
- `manage.py check` sin incidencias.
- Todas las migraciones figuran aplicadas al consultar showmigrations; no se ejecutaron migraciones.
- Lectura ORM de los 21 modelos, incluidas tablas intermedias, sin errores de esquema y sin mostrar datos.
- HTTP verificado por loopback y por 172.16.0.5: redireccion a login, HTML, JavaScript, CSS, logo y recursos del administrador.
- API de sesion sin autenticar responde 401 y entrega cookie CSRF; credenciales de prueba inexistentes responden 401; clientes sin autenticar responde 403. Host desconocido rechazado con 400. No se modificaron registros para estas pruebas.
- Tarea Azure deshabilitada y regla de firewall verificada.

Falta comprobar desde otro dispositivo real de la red e iniciar sesion con un usuario existente de la aplicacion. No se conocen ni se restablecieron sus contrasenas; la contrasena SQL de Azure no es la de los usuarios del sistema. Las pruebas realizadas no incluyen registrar facturas o pagos. No se configuro inicio automatico de Windows ni una copia diaria local nueva.

## Datos y respaldos

BDsofactur es ahora la base principal de escritura, no una copia de recuperacion. Conservar sus respaldos antes de cambios de esquema o de una futura conexion Azure. El BACPAC de validacion local anterior en `.recovery/local-validation.bacpac` es una copia puntual y no se actualiza con los movimientos nuevos. No existe copia diaria activa configurada por esta tarea.

Al retomar Azure, preparar una migracion controlada de los datos locales actuales, verificar saldos y movimientos y acordar el corte. No activar el antiguo proceso Azure-a-local sobre la base principal ni asumir que Azure contiene los movimientos registrados desde este cambio.

Referencias de los componentes de ejecucion: [Waitress para Windows](https://docs.pylonsproject.org/projects/waitress/en/latest/) y [WhiteNoise para Django](https://whitenoise.readthedocs.io/en/stable/django.html).