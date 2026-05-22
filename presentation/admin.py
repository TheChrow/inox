from django.contrib import admin
from infrastructure.models.branch_db import Branch
from infrastructure.models.products_db import Product
from infrastructure.models.seller_db import Seller
from infrastructure.models.seller_type_db import SellerType

# Register your models here.
admin.site.register(SellerType)
admin.site.register(Seller)
admin.site.register(Branch)
admin.site.register(Product)

admin.site.index_title = "Luminox Chile - Administración"
admin.site.site_header = "Luminox Chile - Administración"
admin.site.site_title = "Luminox Chile - Administración"

