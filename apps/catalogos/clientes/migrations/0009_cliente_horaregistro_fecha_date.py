from django.db import migrations, models


def copy_time_from_fecha_registro(apps, schema_editor):
    Cliente = apps.get_model('clientes', 'Cliente')

    for cliente in Cliente.objects.all():
        fecha_registro = cliente.FechaRegistro
        if fecha_registro:
            cliente.HoraRegistro = fecha_registro.time()
            cliente.save(update_fields=['HoraRegistro'])


def clear_hora_registro(apps, schema_editor):
    Cliente = apps.get_model('clientes', 'Cliente')
    Cliente.objects.update(HoraRegistro=None)


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0008_cliente_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='HoraRegistro',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.RunPython(copy_time_from_fecha_registro, clear_hora_registro),
        migrations.AlterField(
            model_name='cliente',
            name='FechaRegistro',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='HoraRegistro',
            field=models.TimeField(auto_now_add=True),
        ),
    ]
