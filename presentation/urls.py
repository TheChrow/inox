from django.urls import path
from presentation.views import views

urlpatterns = [
        path('', views.home, name="home"),
        path('logout/', views.userLogout, name='logout'),
        path('generate-quote/', views.generate_quote, name='generate_quote'),
        path('generate-quote/<str:odoo_name>/', views.generate_quote, name='generate_quote_by_odoo_name'),
        path('list-of-quotes/', views.list_of_quotes, name='list_of_quotes'),
        path('generate-sales-order/', views.generate_sales_order, name='generate_sales_order'),
        path('list-of-sales-orders/', views.list_of_sales_orders, name='list_of_sales_orders'),
        path('list-of-returns/', views.list_of_returns, name='list_of_returns'),
        path('pending-rr/', views.pending_rr, name='pending_rr'),
        path('create-customers/', views.create_customers, name='create_customers'),
        path('list-of-customers/', views.list_of_customers, name='list_of_customers'),
        path('list-of-sales/', views.list_of_sales, name='list_of_sales'),
        path('product-reports/', views.product_reports, name='product_reports'),
        path('my-data/', views.my_data, name='my_data'),
        path('my-account/', views.my_account, name='my_account'),
        path('list-of-users/', views.list_of_users, name='list_of_users'),
        path('guardar_contactos/', views.list_of_users, name='guardar_contactos_ajx'),
        path('search-products/', views.search_products, name='search_products'),
        path('odoo/health/', views.OdooHealthView.as_view(), name='odoo_health'),
        path('odoo/partners/', views.OdooPartnerCreateView.as_view(), name='odoo_partner_create'),
        path('odoo/partners/search/', views.OdooPartnerSearchView.as_view(), name='odoo_partner_search'),
        path('odoo/partners/<int:customer_id>/', views.OdooPartnerReadView.as_view(), name='odoo_partner_read'),
        path('odoo/quotations/', views.OdooQuotationCreateView.as_view(), name='odoo_quotation_create'),
        path('odoo/quotations/list/', views.OdooQuotationListView.as_view(), name='odoo_quotation_list'),
        path('odoo/quotations/<str:odoo_name>/', views.OdooQuotationReadView.as_view(), name='odoo_quotation_read'),
        path('odoo/quotations/<str:odoo_name>/pdf/', views.OdooQuotationPDFView.as_view(), name='odoo_quotation_pdf'),

]