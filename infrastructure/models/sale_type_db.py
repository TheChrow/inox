from django.db import models

class SaleType(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)