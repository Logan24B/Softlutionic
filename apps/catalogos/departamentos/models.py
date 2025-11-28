from django.db import models
class Departamentos(models.Model):
    Nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'departamentos'

        def __str__(self):
            return f"{self.Nombre}"
# Create your models here.
