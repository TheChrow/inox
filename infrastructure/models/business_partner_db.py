from django.db import models

from infrastructure.models.bp_type_db import BPType
from infrastructure.models.customer_type_db import CustomerType
from infrastructure.models.group_bp_db import GroupBP
from infrastructure.models.price_list_db import PriceList


class BusinessPartner(models.Model):
    code = models.CharField(primary_key=True, max_length=255)

    name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    rut = models.CharField(max_length=255)
    email = models.EmailField()

    phone = models.CharField(max_length=18)
    business_activity = models.CharField(max_length=100)

    payment_condition = models.IntegerField()
    term_claims = models.CharField(max_length=255)
    client_export = models.CharField(max_length=255)

    group_bp = models.ForeignKey(GroupBP, on_delete=models.CASCADE)
    customer_type = models.ForeignKey(CustomerType, on_delete=models.CASCADE)
    bp_type = models.ForeignKey(BPType, on_delete=models.CASCADE)
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE)



