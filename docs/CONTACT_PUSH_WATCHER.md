# Detector Django de contactos Mongo

Django revisa cada 15 segundos la colecci?n de notificaciones existente. Solo reclama avisos activos `solicitud_contacto` de origen `api_contacto`, creados en los ?ltimos cinco minutos, en lotes de hasta 20. No copia la colecci?n ni crea nuevas notificaciones. La marca at?mica `contact_push_attempted_at` comparte la exclusi?n con el puente .NET existente y con otros workers.

Reutiliza el emisor Firebase, que verifica cuentas activas, roles SQL actuales, destinatarios y lecturas. La revisi?n corre en un hilo por worker Gunicorn, despu?s de inicializar Django; no se inicia en tests, migraciones o imports. Gunicorn carga `gunicorn.conf.py` desde su directorio de ejecuci?n: https://gunicorn.org/reference/settings/ . Requiere que el App Service ejecute Gunicorn desde la ra?z del proyecto sin reemplazar ese archivo de configuraci?n.

Activaci?n: `CONTACT_PUSH_POLL_ENABLED=true`, `FCM_ENABLED=true`, credenciales Firebase y Mongo configurados en Django. El workflow activa la primera variable. El App Service debe mantenerse en ejecuci?n; si se suspende no se revisa Mongo. Para ejecuci?n independiente de la web se necesita un worker supervisado separado.

La marca acredita un intento, no entrega: el emisor existente es de mejor esfuerzo. Un reinicio despu?s de reclamar o un error de env?o puede perder un push. No se reenv?an avisos hist?ricos ni se garantiza recuperar interrupciones superiores a cinco minutos. Sin dispositivos elegibles no hay entrega. Los permisos, ajustes del canal y No molestar del tel?fono determinan el sonido.

Registros seguros: inicio del detector, cantidad de intentos y clase de error; sin tokens, URI ni datos del contacto. El detector no sustituye una configuraci?n v?lida de Firebase/Mongo/SQL.

Validaci?n local: 57 pruebas Django aprobadas con SQLite en memoria. Cuatro pruebas del detector verifican Firebase desactivado, credenciales ausentes, selecci?n acotada de avisos y m?ximo por lote. Estas pruebas con dobles no prueban entrega Firebase, concurrencia Atlas ni ejecuci?n real en Azure.
