from django.db import models

from infrastructure.models.customer_db import Customer


class CustomerAddress(models.Model):
    INVOICE = "invoice"
    DELIVERY = "delivery"
    OTHER = "other"
    TYPE_CHOICES = [
        (INVOICE, "Invoice"),
        (DELIVERY, "Delivery"),
        (OTHER, "Other"),
    ]

    odoo_id = models.IntegerField(unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=OTHER)
    name = models.CharField(max_length=255, blank=True, default="")
    street = models.CharField(max_length=255)
    street2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    zip = models.CharField(max_length=32, blank=True, default="")
    country_id = models.IntegerField(blank=True, null=True)
    state_id = models.IntegerField(blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer_address"
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"

    def __str__(self):
        return f"[{self.type}] {self.street} ({self.customer.name})"
