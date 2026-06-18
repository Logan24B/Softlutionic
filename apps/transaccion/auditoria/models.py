from django.db import models


class LogAuditoria(models.Model):
    IdLog = models.BigAutoField(primary_key=True)
    Tabla = models.CharField(max_length=128)
    Accion = models.CharField(max_length=20)
    ClavePrincipal = models.CharField(max_length=128, null=True, blank=True)
    Usuario = models.CharField(max_length=128, default='')
    Host = models.CharField(max_length=128, default='')
    Fecha = models.DateTimeField()
    Detalle = models.CharField(max_length=4000, null=True, blank=True)

    class Meta:
        db_table = 'LogAuditoria'
        verbose_name = 'Log de auditoria'
        verbose_name_plural = 'Logs de auditoria'
        ordering = ['-Fecha']

    def __str__(self):
        return f'{self.Tabla} - {self.Accion} - {self.Fecha}'

