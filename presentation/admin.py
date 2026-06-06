from django.contrib import admin
from infrastructure.models.branch_db import Branch
from infrastructure.models.menu_module_db import MenuModule
from infrastructure.models.nav_item_db import NavItem
from infrastructure.models.products_db import Product
from infrastructure.models.seller_db import Seller
from infrastructure.models.seller_type_db import SellerType

# Register your models here.
admin.site.register(SellerType)
admin.site.register(Seller)
admin.site.register(Branch)
admin.site.register(Product)


@admin.register(MenuModule)
class MenuModuleAdmin(admin.ModelAdmin):
    list_display = ('code', 'label_short', 'url_name', 'order', 'is_active', 'group_list')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'groups')
    search_fields = ('code', 'label', 'url_name')
    filter_horizontal = ('groups',)
    ordering = ('order', 'label')

    @admin.display(description='Etiqueta')
    def label_short(self, obj):
        return obj.label.replace('\n', ' / ')

    @admin.display(description='Grupos')
    def group_list(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '—'


class NavItemChildInline(admin.TabularInline):
    model = NavItem
    fk_name = 'parent'
    extra = 0
    fields = ('code', 'label', 'url_name', 'order', 'is_active')
    show_change_link = True


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'parent', 'url_name', 'active_paths', 'order', 'is_active', 'group_list')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'parent', 'groups')
    search_fields = ('code', 'label', 'url_name', 'active_paths')
    filter_horizontal = ('groups',)
    ordering = ('parent__id', 'order', 'label')
    inlines = [NavItemChildInline]

    @admin.display(description='Grupos')
    def group_list(self, obj):
        return ', '.join(g.name for g in obj.groups.all()) or '—'


admin.site.index_title = "Luminox Chile - Administración"
admin.site.site_header = "Luminox Chile - Administración"
admin.site.site_title = "Luminox Chile - Administración"

