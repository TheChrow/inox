from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse

from domain.product_csv_import_service import (
    CsvFormatError,
    csv_template_bytes,
    import_products_from_csv,
)
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


class ProductCsvUploadForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo CSV",
        help_text="Codificación UTF-8. Separador coma. La primera fila debe ser la cabecera.",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "brand", "list_price", "sale_price", "total_stock")
    search_fields = ("code", "name", "brand")
    list_filter = ("brand", "is_discontinued", "is_inactive")
    change_list_template = "admin/infrastructure/product/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="infrastructure_product_import_csv",
            ),
            path(
                "import-csv/plantilla/",
                self.admin_site.admin_view(self.download_template_view),
                name="infrastructure_product_import_csv_template",
            ),
        ]
        return custom + urls

    def download_template_view(self, request):
        response = HttpResponse(csv_template_bytes(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="plantilla_productos.csv"'
        return response

    def import_csv_view(self, request):
        if request.method == "POST":
            form = ProductCsvUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    result = import_products_from_csv(form.cleaned_data["archivo"])
                except CsvFormatError as exc:
                    messages.error(request, f"Error en el archivo: {exc}")
                else:
                    if result.created or result.updated:
                        messages.success(
                            request,
                            f"Productos creados: {result.created} · actualizados: {result.updated}",
                        )
                    for line, error in result.errors:
                        messages.warning(request, f"Fila {line}: {error}")
                    if not result.errors and (result.created or result.updated):
                        return redirect(reverse("admin:infrastructure_product_changelist"))
        else:
            form = ProductCsvUploadForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Cargar productos desde CSV",
            "form": form,
            "opts": self.model._meta,
            "template_url": reverse("admin:infrastructure_product_import_csv_template"),
        }
        return render(request, "admin/infrastructure/product/import_csv.html", context)


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

