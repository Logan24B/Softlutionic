# Inicio automatico de SoftFactur en Windows

Este procedimiento configura Waitress con el Programador de tareas. No instala
un servicio de Windows: crea una tarea persistente que inicia al arrancar el
equipo, sin iniciar sesion. La instalacion solo queda validada despues de probar
un reinicio y acceder desde una PC cliente.

## 1. Requisitos de este servidor

- Proyecto: `C:\Users\softadmin\Desktop\Softlutionic`.
- Python del entorno: `.venv\Scripts\python.exe`.
- Django, Waitress, WhiteNoise y pyodbc disponibles (verificados por importacion).
- SQL Server: instancia `SQLEXPRESS`, base `BDsofactur`.
- Controlador: ODBC Driver 18 for SQL Server.
- IP actual: `172.16.0.5`, autorizada en ALLOWED_HOSTS.
- Reservar esa IP mediante DHCP o configuracion de red para que no cambie.

La conexion actual no declara USER ni PASSWORD. La tarea debe ejecutarse con
una cuenta de Windows autorizada en SQL Server. En este servidor se utilizara
la cuenta con la que ya funciona el sistema: `softlutionic\softadmin`.
No cambiarla por SYSTEM. En otro servidor elegir y autorizar la cuenta local
o de dominio correspondiente. No guardar contrasenas en los scripts.

## 2. Preparar SQL Server

Abrir `services.msc`, localizar SQL Server (SQLEXPRESS), establecer Inicio
automatico e iniciar el servicio. Confirmar que la base BDsofactur existe y
que la cuenta de la tarea puede utilizarla. Si la conexion mediante instancia
con nombre requiere SQL Server Browser, comprobar tambien ese servicio y la
configuracion de red de SQL Server.

## 3. Preparar y probar la aplicacion

En PowerShell, ejecutar cada comando por separado:

```powershell
Set-Location 'C:\Users\softadmin\Desktop\Softlutionic'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe .\start_server.py
```

Detener primero cualquier `runserver` u otro proceso del proyecto que ocupe
el puerto 8000. No continuar si check o collectstatic falla.
No es necesario activar el entorno: se utiliza directamente su Python.

Probar `http://127.0.0.1:8000/` en el servidor y
`http://172.16.0.5:8000/` desde el cliente. Revisar inicio de sesion, una
consulta a la base, estilos, JavaScript e imagenes. WhiteNoise sirve los
archivos estaticos recopilados; no resuelve por si mismo archivos subidos
por usuarios. Si existen cargas de archivos, comprobar su entrega aparte.

El lanzador fuerza DEBUG=false, verifica la base con SELECT 1 y reintenta
hasta 12 veces con pausas de 10 segundos. Cada intento puede consumir ademas
el tiempo de conexion del controlador. Los errores quedan registrados en
`.runtime\logs\server.log`, con rotacion de cinco respaldos de 5 MB.
Tras la prueba detenerlo con Ctrl+C.

## 4. Crear la tarea de inicio

1. Abrir el Programador de tareas como administrador (`taskschd.msc`).
2. Seleccionar Crear tarea, no Crear tarea basica.
3. En General, nombre: `SoftFactur-Web`.
4. Seleccionar la cuenta `softlutionic\softadmin` o la cuenta autorizada
   correspondiente al servidor.
5. Seleccionar Ejecutar tanto si el usuario inicio sesion como si no.
   Dejar desmarcado No almacenar contrasena. No se necesita Ejecutar con
   los privilegios mas altos para la aplicacion.
6. En Desencadenadores, crear uno Al iniciar el sistema, con retraso
   de 1 minuto y habilitado.
7. En Acciones, seleccionar Iniciar un programa:
   - Programa: `C:\Users\softadmin\Desktop\Softlutionic\.venv\Scripts\python.exe`
   - Argumentos: `"C:\Users\softadmin\Desktop\Softlutionic\start_server.py"`
   - Iniciar en: `C:\Users\softadmin\Desktop\Softlutionic`
8. En Condiciones, desmarcar iniciar solo si esta inactivo y las restricciones
   de alimentacion que impidan mantener el sistema disponible.
9. En Configuracion, permitir ejecucion a peticion; reiniciar si falla cada
   minuto hasta 999 veces; desmarcar detener si dura mas de un tiempo;
   si ya se esta ejecutando, No iniciar una instancia nueva.
10. Guardar e introducir la contrasena de Windows de la cuenta seleccionada
    en el dialogo del sistema. No es el PIN. Si la politica del equipo niega
    el inicio como trabajo por lotes, el administrador debe autorizarlo.

La cuenta debe poder leer el proyecto y el entorno y escribir en `.runtime`.
Si cambia su contrasena, actualizar las credenciales guardadas de la tarea.

## 5. Red y prueba de arranque

El acceso desde cliente ya funciono en este servidor. Si en otro servidor
falta una regla, crear en PowerShell como administrador:

```powershell
New-NetFirewallRule -DisplayName 'SoftFactur TCP 8000 LAN' -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress LocalSubnet -Action Allow
```

LocalSubnet permite la subred local. Si los clientes estan en otra subred,
el administrador debe definir los rangos autorizados y sus rutas.

1. Ejecutar manualmente la tarea SoftFactur-Web y comprobar acceso cliente.
2. Revisar `.runtime\logs\server.log` y el Historial de la tarea si falla.
3. Reiniciar el servidor en una ventana de mantenimiento.
4. Sin iniciar sesion, esperar el arranque de Windows, SQL Server y la tarea.
5. Desde un cliente probar acceso, inicio de sesion, consulta y estaticos.
6. Solo dar por terminada la instalacion si esta prueba funciona.

La tarea debe permanecer En ejecucion; 0x41301 indica que sigue ejecutandose.
Para mantenimiento, finalizar la tarea y verificar que el puerto se libera.
Para desactivar el arranque, deshabilitar la tarea. No arrancar runserver
mientras Waitress este utilizando el mismo puerto.

## 6. Instalacion en otro servidor

No copiar `.venv`: crear un entorno nuevo con Python compatible e instalar
las dependencias del proyecto. Verificar versiones y compatibilidad antes
de usar esta instalacion como referencia de produccion. requirements.txt
contiene rangos y por si solo no reproduce exactamente las versiones.

Instalar ODBC Driver 18 y SQL Server; restaurar o preparar BDsofactur;
autorizar la cuenta de ejecucion; adaptar database_config.py al servidor.
Configurar una IP estable y agregarla mediante SOFTFACTUR_ALLOWED_HOSTS
o ALLOWED_HOSTS. Cambiar las tres rutas de la accion de la tarea segun la
ubicacion del proyecto. Repetir recopilacion de estaticos y todas las pruebas.
No ejecutar migraciones o restauraciones sobre datos existentes sin revisar
el esquema y disponer de respaldo. Este documento no sustituye el plan de
respaldo ni la revision de seguridad previa a exponer el sistema en Internet.
