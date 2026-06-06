from django.db import models

from infrastructure.models.customer_db import Customer


class CustomerContact(models.Model):
    odoo_id = models.IntegerField(unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    name = models.CharField(max_length=255)
    function = models.CharField(max_length=128, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer_contact"
        verbose_name = "Customer Contact"
        verbose_name_plural = "Customer Contacts"

    def __str__(self):
        return f"{self.name} -> {self.customer.name}"
