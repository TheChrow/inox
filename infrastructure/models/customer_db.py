from django.db import models


class Customer(models.Model):
    odoo_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=255)
    is_company = models.BooleanField(default=False)

    vat = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=64, blank=True, default="")
    website = models.CharField(max_length=255, blank=True, default="")
    comment = models.TextField(blank=True, default="")

    street = models.CharField(max_length=255, blank=True, default="")
    street2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    zip = models.CharField(max_length=32, blank=True, default="")
    country_id = models.IntegerField(blank=True, null=True)
    state_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.name} ({self.vat or self.odoo_id})"
