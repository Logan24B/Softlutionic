# ARCHIVO HISTORICO: Azure pospuesto; no aplicar esta configuracion

La configuracion activa es exclusivamente local. Consultar RECUPERACION_SQL.md en la raiz. Los scripts Azure estan bloqueados y su tarea deshabilitada.

# Azure principal y recuperacion local

## Estado de la implementacion (16 octubre 2026)

Proyecto Django 4.2 con mssql-django y backend existente sin MARS. No se encontraron AGENTS.md en el proyecto ni en sus directorios superiores consultados. El arbol Git estaba limpio al comenzar.

Azure es ahora el destino predeterminado: `tcp:sql-softlutionic2.database.windows.net,1433`, base `softlutionic-sistema-db`, usuario SQL `softadmin`, cifrado habilitado, certificado validado y timeout de conexion de 30 segundos. La configuracion encontrada era Windows/local; no contenia Active Directory Default. No se ejecutan migraciones, inicializaciones ni replicacion de escrituras. No hay conmutacion automatica. Sin secreto la aplicacion falla al configurar la conexion.

Se conserva `BDsofactur` como destino de recuperacion en `localhost\SQLEXPRESS`. Comprobado: SQL Express 2025 17.0.1000.7, ODBC 18 x64, base ONLINE de aproximadamente 80 MB, 84.8 GB libres en C:, acceso Windows como `SOFTLUTIONIC\softadmin`, zona Windows `Central America Standard Time` (UTC-6 sin horario de verano), puerto Azure 1433 accesible. Esto NO acredita autenticacion Azure ni compatibilidad de sus datos.

Instalado SqlPackage/DacFx .NET Framework 170.4.83.3 desde instalador oficial Microsoft con firma valida. El proceso usa la misma API DacFx en memoria para evitar contrasenas en argumentos de procesos. Preparado `.venv` con Python 3.11.17 y los requisitos existentes: Django 4.2, mssql-django 1.8.0 y pyodbc 5.3.0, entre otros. No se modifico requirements.txt.

Pruebas ejecutadas: sintaxis Python y PowerShell, aserciones de destino/autenticacion/cifrado/timeout Azure con credencial sintetica y rechazo de modo invalido; `git diff --check`; exportacion DacFx de BDsofactur, importacion de 22 tablas en una base de prueba unica y CHECKDB exitoso. Solo se elimino esa base de prueba creada por la verificacion; BDsofactur permanece intacta. El BACPAC de prueba queda protegido en `.recovery\local-validation.bacpac`. Se corrigio la construccion de conexion .NET en PowerShell para usar nombres de clave SQL validos. `manage.py check` paso sin incidencias. La credencial proporcionada se guardo en privado; tanto .NET SqlClient como Django/ODBC recibieron de Azure el error 18456 (login rechazado para softadmin); Django reporto SQLSTATE 28000. `-CheckOnly` falla en `connections`, registrado en `.recovery\last-check.json`. No se crearon temporales Azure ni se sustituyo BDsofactur. Falta una credencial aceptada para probar el flujo completo.

## Configuracion privada y arranque

Desde PowerShell, en el directorio del proyecto:

```powershell
.\scripts\Set-AzureSecret.ps1
```

Captura oculta; guarda `.private\azure.json` fuera de Git, protegido por ACL para la identidad que lo crea y SYSTEM. Es un archivo privado con el secreto en texto: no compartirlo, adjuntarlo, sincronizarlo ni habilitar transcripciones al capturarlo. La cuenta de la aplicacion y la tarea deben poder leerlo; usar la misma identidad o conceder lectura solo a las identidades elegidas. La credencial recibida ya esta guardada alli, pero Azure la rechazo. Django permite cambiar su ubicacion con `SOFTFACTUR_PRIVATE_CONFIG`; el proceso de copia utiliza la ruta fija anterior.

En el entorno Python compatible del proyecto, instalar `requirements.txt` y ejecutar `python manage.py check`, luego una consulta de solo lectura mediante `django.db.connection` para verificar backend/ODBC. Arranque de desarrollo: `python manage.py runserver`; produccion debe conservar su servicio WSGI y entorno. `main.py` es solo un ejemplo, no inicia Django. No ejecutar `migrate`, scripts de creacion ni restauraciones sobre Azure. No registrar cadenas de conexion ni excepciones que puedan incluirlas.

El entorno aislado ya permite estas comprobaciones sin activacion:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\check_database.py
```

El segundo comando consulta solo nombre y edicion del servidor, o informa codigos de error depurados. Para corregir el bloqueo actual, verificar en Azure que softadmin es el usuario SQL del servidor indicado, que la contrasena corresponde y que el usuario tiene acceso a softlutionic-sistema-db; actualizarla mediante Set-AzureSecret.ps1 y repetir las pruebas. No se cambio ni restablecio ninguna credencial en Azure.

## Copia manual y tarea diaria

```powershell
powershell.exe -NoProfile -File .\scripts\Copy-AzureToLocal.ps1 -CheckOnly
powershell.exe -NoProfile -File .\scripts\Copy-AzureToLocal.ps1 -AuthorizeAzureCopyCost -ConfirmReplaceBDsofactur
Get-Content .\.recovery\last-result.json
Get-Content .\.recovery\last-check.json
Get-Content .\.recovery\history.jsonl -Tail 10
```

El usuario autorizo sustituir el nombre local conservando la anterior y probar una copia temporal facturable con sus creditos de estudiante. Todavia no se ha creado ningun recurso Azure. Una copia temporal tiene costo de computo/almacenamiento segun el nivel de la base; no es posible dar un importe sin acceso a su configuracion y tarifas. Revisar credito y nivel antes de activar recurrencia.

Flujo: bloqueo exclusivo de archivo; conexiones y capacidad Express (50 GB para 2025, 10 GB en versiones anteriores, margen del 15%); espacio en volumen de archivos y de datos/log local (minimo 5 GB o cinco veces los datos Azure asignados); copia Azure unica `softlutionic_recovery_<UTC>_<id>`; esperar ONLINE; exportar BACPAC desde esa copia sin escrituras de aplicacion; importar en `BDsofactur_candidate_<id>`; comparar tablas y conteos exactos con la copia Azure; CHECKDB y CHECKCONSTRAINTS; rechazar sesiones locales activas; renombrar BDsofactur a `BDsofactur_previous_<id>` y promover candidata. Si falla el segundo renombrado, intenta restaurar el anterior. Nunca borra bases locales. La importacion DacFx valida compatibilidad de esquema con el servidor destino; una importacion fallida no reemplaza la copia valida. Conteos y CHECKDB no sustituyen pruebas funcionales de la aplicacion.

La copia consistente Azure se elimina en finally. Una interrupcion forzada, caida del host o perdida de permisos puede impedir limpieza: consultar `cleanupFailed` y el nombre `azureCopy`; revisar en Azure y eliminar exclusivamente la temporal identificada despues de confirmar propiedad. No eliminar la base principal. Una temporal que permanezca sigue consumiendo creditos. La cuenta SQL necesita permisos para copiar y eliminar sus temporales y leer tablas; la identidad local necesita crear, validar y renombrar bases. No se han concedido permisos automaticamente.

La tarea `Softlutionic-AzureToLocal-Daily` esta registrada DESHABILITADA a las 00:00 locales. Su identidad provisional es el usuario actual, con inicio interactivo; esto no garantiza ejecucion sin sesion. Una vez exitosa la primera copia manual:

```powershell
.\scripts\Register-RecoveryTask.ps1 -EnableWithPassword
Start-ScheduledTask -TaskName Softlutionic-AzureToLocal-Daily
Get-ScheduledTaskInfo -TaskName Softlutionic-AzureToLocal-Daily
Get-ScheduledTask -TaskName Softlutionic-AzureToLocal-Daily | Select-Object State,Principal,Triggers
```

La activacion captura credenciales WINDOWS de la misma cuenta, que Windows almacena para ejecutar sin sesion (no son las de Azure). Requiere derecho de inicio de sesion por lotes y permisos SQL/local/archivo. No asumir que crear la tarea comprueba ese derecho: verificar una ejecucion desde el Programador y `LastTaskResult=0`, ademas del JSON `stage=success` y `cleanupFailed=false`. No ejecutar copia con recuperacion activa. La tarea evita instancias simultaneas y recupera horarios perdidos al volver a encender el host; limite de seis horas. El bloqueo de archivo tambien protege ejecuciones manuales. El limite forzado puede dejar recursos temporales; revisar resultados y Azure si ocurre.

Retencion: BACPAC antiguos de mas de siete dias se eliminan solo tras copia exitosa; el archivo recien validado siempre se conserva. Bases previas/candidatas nunca se purgan automaticamente: revisar semanalmente, conservar al menos la ultima valida anterior, y autorizar individualmente cualquier eliminacion verificando nombre, fecha y estado de recuperacion. El espacio insuficiente detiene la copia sin borrar la anterior. Los JSON historicos se conservan para diagnostico; archivarlos periodicamente. BACPAC y archivos SQL contienen datos sensibles, protegidos por ACL; usar BitLocker/cifrado del volumen para proteccion en reposo. No son backups .bak descargables de Azure.

## Activar recuperacion controlada

1. Detener escrituras y todos los procesos de la aplicacion. Deshabilitar la tarea. Confirmar fecha/resultado de la ultima copia y aceptar perdida potencial de aproximadamente 24 horas mas la duracion de copia, o mas si hubo fallas. Validar usuarios y funciones necesarias en la copia local.
2. Crear `.private\recovery-active` y configurar `SOFTFACTUR_DB_MODE=local-recovery` en el entorno real del servicio; reiniciar y comprobar que usa BDsofactur. El marcador bloquea nuevas copias; el modo local exige el marcador. Mantener Azure sin escrituras concurrentes de esta aplicacion. Registrar hora, ultimo movimiento Azure conocido y todos los movimientos nuevos locales.
3. Antes de regresar: detener escrituras locales; preservar una copia adicional de la base y un inventario de movimientos locales con identificadores, fechas y auditoria. Reconciliar contra Azure por reglas de negocio, resolver duplicados, secuencias y conflictos, ensayar y validar totales/saldos. No importar la base local sobre Azure ni reanudar Azure descartando movimientos locales. Este proyecto no implementa sincronizacion automatica ni reconciliacion.
4. Tras aprobacion de la reconciliacion, quitar la variable de modo local, reiniciar contra Azure y verificar con consultas/pruebas funcionales. Quitar el marcador solo al terminar la recuperacion y reactivar la tarea. Conservar evidencia y la base local usada durante recuperacion.

Si el host cae entre renombrados, el diario puede quedar incompleto: inspeccionar sys.databases; si falta BDsofactur, recuperar el nombre desde la anterior identificada tras confirmar destino y detener consumidores. No borrar bases para resolverlo.

## Referencias oficiales

- [Exportacion BACPAC y consistencia](https://learn.microsoft.com/en-us/azure/azure-sql/database/database-export?view=azuresql)
- [Copia consistente de Azure SQL](https://learn.microsoft.com/en-us/azure/azure-sql/database/database-copy?view=azuresql)
- [SqlPackage y API DacFx](https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-download)
- [Limites SQL Express 2025](https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-latest)

Pendientes: resolver rechazo de login Azure, verificar permisos/tamano Azure, primera exportacion/importacion desde Azure y prueba funcional, identidad no interactiva y ejecucion real de tarea antes de habilitar la proteccion diaria. La copia diaria todavia no esta operativa.
