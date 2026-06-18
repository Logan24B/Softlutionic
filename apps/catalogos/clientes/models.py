from django.db import models
from django.db.models import Q
from django.core.validators import RegexValidator


telefono_validator = RegexValidator(
    regex=r'^\+505 [0-9]{4} [0-9]{4}$',
    message='El telefono debe tener formato nicaraguense: +505 0000 0000.',
)

cedula_validator = RegexValidator(
    regex=r'^\d{3}-?\d{6}-?\d{4}[A-Za-z]$',
    message='La cedula debe tener formato nicaraguense, por ejemplo 001-010190-0001A.',
)


class Cliente(models.Model):
    DepartamentoId = models.ForeignKey(
        'departamentos.Departamentos',
        on_delete=models.PROTECT,
        related_name='clientes',
        db_column='DepartamentoId',
    )
    Nombre = models.CharField(max_length=50)
    Apellido = models.CharField(max_length=50)
    Cedula = models.CharField(max_length=20, null=True, blank=True, validators=[cedula_validator])
    Telefono = models.CharField(max_length=25, unique=True, validators=[telefono_validator])
    Direccion = models.CharField(max_length=100)
    FechaRegistro = models.DateField(auto_now_add=True)
    HoraRegistro = models.TimeField(auto_now_add=True)
    Correo = models.EmailField(max_length=50, unique=True)
    Estado = models.BooleanField(default=True)

    class Meta:
        db_table = 'Clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['Nombre', 'Apellido']
        constraints = [
            models.UniqueConstraint(
                fields=['Cedula'],
                condition=Q(Cedula__isnull=False),
                name='uq_clientes_cedula_not_null',
            ),
        ]

    def __str__(self):
        return f'{self.Nombre} {self.Apellido}'
