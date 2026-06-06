from django.contrib.auth.models import Group
from django.db import models


class MenuModule(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    label = models.TextField()
    url_name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, related_name='menu_modules', blank=True)

    class Meta:
        verbose_name = 'Módulo de menú'
        verbose_name_plural = 'Módulos de menú'
        ordering = ['order', 'label']
        db_table = 'menu_module'

    def __str__(self):
        return self.label.replace('\n', ' ')
