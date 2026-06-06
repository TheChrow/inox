from django.conf import settings
from django.db import migrations, models


SEED_MODULES = [
    # (code, label, url_name, order, group_names)
    ('generate_quote',        'Generar\nCotización',       'generate_quote',        10,  ['Admin', 'Seller']),
    ('list_of_quotes',        'Listar\nCotizaciones',      'list_of_quotes',        20,  ['Admin', 'Seller']),
    ('generate_sales_order',  'Generar Orden\nde Venta',   'generate_sales_order',  30,  ['Admin', 'Seller']),
    ('list_of_sales_orders',  'Listar Órdenes\nde Venta',  'list_of_sales_orders',  40,  ['Admin', 'Seller']),
    ('create_customers',      'Registrar\nCliente',        'create_customers',      50,  ['Admin', 'Seller']),
    ('list_of_customers',     'Listar\nClientes',          'list_of_customers',     60,  ['Admin', 'Seller']),
    ('list_of_sales',         'Consultar\nVentas',         'list_of_sales',         70,  ['Admin', 'Seller']),
    ('analytics_products',    'Analítica de\nProductos',   'product_reports',       80,  ['Admin', 'Seller']),
    ('my_data',               'Administrar\nPerfil',       'my_data',               90,  ['Admin', 'Seller']),
    ('list_of_returns',       'Solicitudes\nDevolución',   'list_of_returns',       100, ['Admin', 'Supervisor', 'Seller']),
    ('pending_rr',            'Solicitudes\nPendientes',   'pending_rr',            110, ['Admin', 'Supervisor']),
    ('my_account',            'Configuración\nde Cuenta',  'my_account',            120, ['Admin']),
    ('list_of_users',         'Gestión de\nUsuarios',      'list_of_users',         130, ['Admin']),
    ('product_reports_comex', 'Reportes de\nProductos',    'product_reports',       140, ['Comex']),
]


def seed_modules(apps, schema_editor):
    MenuModule = apps.get_model('infrastructure', 'MenuModule')
    Group = apps.get_model('auth', 'Group')

    for code, label, url_name, order, group_names in SEED_MODULES:
        module, _ = MenuModule.objects.update_or_create(
            code=code,
            defaults={
                'label': label,
                'url_name': url_name,
                'order': order,
                'is_active': True,
            },
        )
        groups = [Group.objects.get_or_create(name=name)[0] for name in group_names]
        module.groups.set(groups)


def unseed_modules(apps, schema_editor):
    MenuModule = apps.get_model('infrastructure', 'MenuModule')
    MenuModule.objects.filter(code__in=[row[0] for row in SEED_MODULES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0002_discountconfig_product'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=80, unique=True)),
                ('label', models.TextField()),
                ('url_name', models.CharField(max_length=80)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='menu_modules', to='auth.group')),
            ],
            options={
                'verbose_name': 'Módulo de menú',
                'verbose_name_plural': 'Módulos de menú',
                'db_table': 'menu_module',
                'ordering': ['order', 'label'],
            },
        ),
        migrations.RunPython(seed_modules, unseed_modules),
    ]
