from django.db import models


class SellerType(models.Model):
    code = models.IntegerField()
    name = models.CharField(max_length=100)