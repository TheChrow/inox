from django.db import models

class Product(models.Model):
    class Meta:
        db_table = "product"
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    code = models.CharField(primary_key=True, max_length=50, unique=True)
    name = models.CharField(max_length=255, null=False)
    image_url = models.CharField(
        max_length=255,
        default="https://ledstudiocl.vtexassets.com/assets/vtex.file-manager-graphql/images/14ecba9f-2814-4029-9e0e-e5e6b9e2869c___b2a5497dbc81c0adc5576c48b2eeb27b.jpg"
    )
    total_stock = models.IntegerField(default=0, null=False)
    list_price = models.FloatField(null=False)
    sale_price = models.FloatField(null=False)
    max_store_discount = models.FloatField()
    max_project_discount = models.FloatField()
    product_url = models.CharField(max_length=255, null=False)
    brand = models.CharField(max_length=20, default="No Brand", null=True)
    cost = models.FloatField(default=0, null=False)
    is_discontinued = models.CharField(max_length=10, default='0', null=True)
    is_inactive = models.CharField(max_length=10, default='NO', null=True)
    tree_type = models.CharField(max_length=50, default='DEFAULT', null=True)
    certification = models.CharField(max_length=100, default='4', null=True)
    image_status_http = models.IntegerField(null=True, blank=True, default=9999)

    def __str__(self):
        return self.code