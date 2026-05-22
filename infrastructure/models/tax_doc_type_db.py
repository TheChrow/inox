from django.db import models

class TaxDocumentType(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
