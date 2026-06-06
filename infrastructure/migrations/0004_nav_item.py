import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


# (code, label, url_name, active_paths, parent_code, order, group_names)
SEED_NAV_ITEMS = [
    ('nav_quotes',         'Cotizaciones',       'list_of_quotes',       'list-of-quotes,generate-quote',             None,            10,  ['Admin', 'Seller']),
    ('nav_sales_orders',   'Órdenes de Venta',   'list_of_sales_orders', 'list-of-sales-orders,generate-sales-order', None,            20,  ['Admin', 'Seller']),
    ('nav_customers',      'Clientes',           'list_of_customers',    'list-of-customers,create-customers',        None,            30,  ['Admin', 'Seller']),
    ('nav_sales',          'Consulta de Ventas', 'list_of_sales',        '',                                          None,            40,  ['Admin', 'Seller']),
    ('nav_stock_report',   'Reporte Stock',      'product_reports',      '',                                          None,            50,  ['Admin', 'Seller']),
    ('nav_returns',        'Devoluciones',       '',                     'list-of-returns,pending-rr',                None,            60,  ['Admin', 'Seller', 'Supervisor', 'Comex']),
    # children of nav_returns
    ('nav_returns_pending',  'Solicitudes Pendientes', 'pending_rr',      '',                                         'nav_returns',   10,  ['Admin', 'Supervisor']),
    ('nav_returns_approved', 'Solicitudes Aprobadas',  'list_of_returns', '',                                         'nav_returns',   20,  ['Admin', 'Seller', 'Supervisor', 'Comex']),
]


def seed_nav_items(apps, schema_editor):
    NavItem = apps.get_model('infrastructure', 'NavItem')
    Group = apps.get_model('auth', 'Group')

    # First pass: create/update everything without parent assignment
    for code, label, url_name, active_paths, parent_code, order, group_names in SEED_NAV_ITEMS:
        item, _ = NavItem.objects.update_or_create(
            code=code,
            defaults={
                'label': label,
                'url_name': url_name,
                'active_paths': active_paths,
                'order': order,
                'is_active': True,
            },
        )
        groups = [Group.objects.get_or_create(name=name)[0] for name in group_names]
        item.groups.set(groups)

    # Second pass: wire up parents now that all rows exist
    for code, _, _, _, parent_code, _, _ in SEED_NAV_ITEMS:
        if parent_code:
            parent = NavItem.objects.get(code=parent_code)
            NavItem.objects.filter(code=code).update(parent=parent)


def unseed_nav_items(apps, schema_editor):
    NavItem = apps.get_model('infrastructure', 'NavItem')
    NavItem.objects.filter(code__in=[row[0] for row in SEED_NAV_ITEMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0003_menu_module'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NavItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=80, unique=True)),
                ('label', models.CharField(max_length=80)),
                ('url_name', models.CharField(blank=True, max_length=80)),
                ('active_paths', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='children',
                    to='infrastructure.navitem',
                )),
                ('groups', models.ManyToManyField(blank=True, related_name='nav_items', to='auth.group')),
            ],
            options={
                'verbose_name': 'Ítem de navegación',
                'verbose_name_plural': 'Ítems de navegación',
                'db_table': 'nav_item',
                'ordering': ['order', 'label'],
            },
        ),
        migrations.RunPython(seed_nav_items, unseed_nav_items),
    ]
