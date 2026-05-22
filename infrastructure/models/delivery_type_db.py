from django.db import models

class DeliveryType(models.Model):
    code = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
