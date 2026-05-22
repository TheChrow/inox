from django.db import models

class PaymentTerms(models.Model):
    code = models.IntegerField()
    name = models.CharField(max_length=50)