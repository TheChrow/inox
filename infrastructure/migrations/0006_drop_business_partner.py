import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0005_customer_contact_address'),
    ]

    # Document tiene 0 filas; agregamos la nueva FK como NULL y luego
    # la promovemos a NOT NULL para no necesitar default.
    operations = [
        migrations.RemoveField(
            model_name='document',
            name='business_partner',
        ),
        migrations.DeleteModel(
            name='BusinessPartner',
        ),
        migrations.AddField(
            model_name='document',
            name='customer',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='infrastructure.customer',
            ),
        ),
        migrations.AlterField(
            model_name='document',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='infrastructure.customer',
            ),
        ),
    ]
