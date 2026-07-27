from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0009_customer_address_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='ref',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='customer',
            name='activity_description',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
