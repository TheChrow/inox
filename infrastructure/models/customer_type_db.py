from django.db import models

class CustomerType(models.Model):
    code = models.CharField(max_length=1)
    name = models.CharField(max_length=50)