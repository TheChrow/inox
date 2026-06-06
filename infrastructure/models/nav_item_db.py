from django.contrib.auth.models import Group
from django.db import models


class NavItem(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=80)
    url_name = models.CharField(
        max_length=80,
        blank=True,
        help_text='Nombre de la URL Django. Déjalo vacío si el ítem solo abre un dropdown.',
    )
    active_paths = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            'Segmentos de URL (kebab-case) separados por coma para resaltar el ítem '
            'como activo, ej: "list-of-quotes,generate-quote". Si está vacío se '
            'deriva automáticamente de url_name.'
        ),
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, related_name='nav_items', blank=True)

    class Meta:
        verbose_name = 'Ítem de navegación'
        verbose_name_plural = 'Ítems de navegación'
        ordering = ['order', 'label']
        db_table = 'nav_item'

    def __str__(self):
        return f"{self.parent.label} / {self.label}" if self.parent_id else self.label

    def active_path_list(self):
        """Lista de segmentos kebab-case para usar en data-page."""
        if self.active_paths:
            return [p.strip() for p in self.active_paths.split(',') if p.strip()]
        if self.url_name:
            return [self.url_name.replace('_', '-')]
        return []
