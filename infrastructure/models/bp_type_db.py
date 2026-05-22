from django.db import models


class BPType(models.Model):
    code = models.CharField(max_length=1)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
