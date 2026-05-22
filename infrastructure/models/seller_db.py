from django.db import models
from django.contrib.auth.models import User
from infrastructure.models.branch_db import Branch
from infrastructure.models.seller_type_db import SellerType


class Seller(models.Model):
    code = models.IntegerField()

    seller_type = models.ForeignKey(SellerType, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.auth_user.first_name} {self.auth_user.last_name} - {self.code}"