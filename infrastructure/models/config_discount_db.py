from django.db import models

class DiscountConfig(models.Model):
    class Meta:
        db_table = "discount_config"
        verbose_name = 'Discount Config'
        verbose_name_plural = 'Discount Configs'

    code = models.CharField(primary_key=True, max_length=50, null=False)
    description = models.CharField(max_length=50, null=False)
    sale_type = models.CharField(max_length=50, null=False)
    max_discount_limit = models.IntegerField(null=False)
    brand_type = models.CharField(max_length=50, null=False)

    def __str__(self):
        return f"{self.code} - {self.description} - {self.sale_type} - {self.max_discount_limit} - {self.brand_type}"