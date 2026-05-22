from django.db import models


class PriceList(models.Model):
    code_list = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    last_modification = models.DateTimeField(auto_now=True)
    list_only_for_members = models.BooleanField(default=False)