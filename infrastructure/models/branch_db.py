from django.db import models

class Branch(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    ubication = models.CharField(max_length=100)