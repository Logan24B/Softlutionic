from django.db import migrations


def seed_tipos_contrato(apps, schema_editor):
    TipoContrato = apps.get_model('contratos', 'TipoContrato')
    Contrato = apps.get_model('contratos', 'Contrato')

    mensual, _ = TipoContrato.objects.get_or_create(
        Nombre='Servicio mensual',
        defaults={'Descripcion': 'Contrato recurrente para servicios mensuales.'},
    )
    unico, _ = TipoContrato.objects.get_or_create(
        Nombre='Servicio unico',
        defaults={'Descripcion': 'Contrato para una prestacion puntual de servicio.'},
    )
    soporte, _ = TipoContrato.objects.get_or_create(
        Nombre='Soporte tecnico',
        defaults={'Descripcion': 'Contrato orientado a soporte, asistencia y mantenimiento.'},
    )

    for contrato in Contrato.objects.filter(TipoContratoId__isnull=True):
        descripcion = (contrato.Descripcion or '').lower()
        tipo = mensual
        if 'unico' in descripcion or 'individual' in descripcion:
            tipo = unico
        elif 'soporte' in descripcion or 'mantenimiento' in descripcion:
            tipo = soporte

        contrato.TipoContratoId = tipo
        contrato.save(update_fields=['TipoContratoId'])


def unseed_tipos_contrato(apps, schema_editor):
    Contrato = apps.get_model('contratos', 'Contrato')
    TipoContrato = apps.get_model('contratos', 'TipoContrato')
    Contrato.objects.update(TipoContratoId=None)
    TipoContrato.objects.filter(
        Nombre__in=['Servicio mensual', 'Servicio unico', 'Soporte tecnico']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contratos', '0002_tipocontrato_contrato_tipocontratoid'),
    ]

    operations = [
        migrations.RunPython(seed_tipos_contrato, unseed_tipos_contrato),
    ]
