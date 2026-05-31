from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import math

from adapters.odoo.factory import get_odoo_client
from adapters.odoo.service.odoo_service_connection import OdooConnectionService
from infrastructure.models.config_discount_db import DiscountConfig
from infrastructure.models.products_db import Product
from infrastructure.models.seller_db import Seller


# Create your views here.
@login_required
def home(request):
    if request.user.is_authenticated:
        username = request.user.username
        name_user = request.user.first_name

        try:
            usuario = Seller.objects.get(auth_user=request.user)

        except Seller.DoesNotExist:
            return JsonResponse({'error': 'User related to authenticated user not found'}, status=404)
        
        context = {
            'username': username,
            'nameUser': name_user,
        }

        return render(request, 'home.html', context)
    


@login_required
def userLogout(request):
    """
    Finaliza la sesion del usuario.

    Args: 
        request (HttpsRequest): La peticion HTTP recibida

    Returns: 
        HttpResponse: redirige a la pagina de inicio despues de cerrar la sesion del usuario.
    """

    logout(request)
    return redirect('/')


def generate_quote(request):

    if request.user.is_authenticated:
        username = request.user.username

        try:
            usuario = Seller.objects.get(auth_user=request.user)
            sucurs = usuario.branch.name  
            nombreUser = usuario.auth_user.first_name
            codVen = usuario.code
            
        except Seller.DoesNotExist:
            return JsonResponse({'error': 'No se encontró el usuario relacionado con el usuario autenticado'}, status=404)

        doc_num = request.GET.get('docNum', None)

        #regiones = RegionDB.objects.all()
        regiones = [{'id': 1, 'nombre': 'Región Metropolitana'},]

        context = {
            'docnum': doc_num,
            'username': username,
            'regiones': regiones,
            'sucursal': sucurs,
            'nombreuser': nombreUser,
            'codigoVendedor': codVen
        }

        # Renderiza el template con el contexto
        return render(request, 'quotation.html', context)
    
def list_of_quotes(request):
    return HttpResponse()

def generate_sales_order(request):
    return HttpResponse()

def list_of_sales_orders(request):
    return HttpResponse()

def list_of_returns(request):
    return HttpResponse()

def pending_rr(request):
    return HttpResponse()

def create_customers(request):
    return HttpResponse()

def list_of_customers(request):
    return HttpResponse()

def list_of_sales(request):
    return HttpResponse()

def product_reports(request):
    return HttpResponse()

def my_data(request):
    return HttpResponse()

def my_account(request):
    return HttpResponse()

def list_of_users(request):
    return HttpResponse()


class OdooHealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        service = OdooConnectionService(get_odoo_client())
        result = service.ping()
        http_status = status.HTTP_200_OK if result.get("ok") else status.HTTP_502_BAD_GATEWAY
        return Response(result, status=http_status)


def search_products(request):

    if request.method == 'GET' and 'numero' in request.GET:
    
        numero = request.GET.get('numero', '').strip()
    
        users_data = user_data(request)

        resultados = Product.objects.filter(
            Q(code__icontains=numero) | Q(name__icontains=numero)
        ).only(
            'code', 'name', 'image_url', 'sale_price', 'total_stock',
            'list_price', 'is_discontinued', 'is_inactive', 'cost'
        )[:20]

        resultados_formateados = []
    
        for p in resultados:
            if p.sale_price > 0 and p.is_inactive != "tYES":
                # inicializar el servicio de listas de precio
                #list_prices = ListPriceService(p.code, p.cost, users_data, card_code)
                #new_price, new_discounted_price = list_prices.get_list_price_info()
                new_price = 0.0  # valores por defecto
                new_discounted_price = 0.0

                # valores por defecto
                precio = p.sale_price
                max_descuento = limitar_descuento(p, users_data, 0.0, 0.0)  # Llamada inicial con 0.0 para evitar errores

                # integrar tu lógica:
                if new_price != 0.0:
                    precio = new_price
                    max_descuento = limitar_descuento(p, users_data, new_price, new_discounted_price)

                resultados_formateados.append({
                    'codigo': p.code,
                    'nombre': p.name + " (Descontinuado)" if p.is_discontinued == "1" else p.name,
                    'imagen': p.image_url,
                    'precio': precio,
                    'stockTotal': p.total_stock,
                    'precioAnterior': p.list_price,
                    'maxDescuento': max_descuento,
                })

        return JsonResponse({'resultados': resultados_formateados})
    else:
        return JsonResponse({'error': 'No se proporcionó un número válido'})

def user_data(request):
    user = request.user

    seller = Seller.objects.get(auth_user=user)

    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'is_active': user.is_active,
        'vendedor': seller.code,
        'tipoVendedor': seller.seller_type.code
    }

def limitar_descuento(producto, users_data, new_price, new_discounted_price):
    """
    Limita el descuento máximo según el tipo de producto y tipo de vendedor.
    El valor límite se obtiene desde la base de datos ConfiDescuentosDB según un código:
        - codigo = '1' → vendedor NO 'P' y marca 'LST'
        - codigo = '2' → vendedor 'P' y marca 'LST'
        - codigo = '3' → vendedor NO 'P' y otra marca
        - codigo = '4' → vendedor 'P' y otra marca
    """

    if users_data['tipoVendedor'] == 'P':
        if producto.brand == 'LST':
            codigo = '2'  # vendedor 'P' y marca 'LST'
        else:
            codigo = '4'  # vendedor 'P' y otra marca
    else:
        if producto.brand == 'LST':
            codigo = '1'  # vendedor distinto de 'P' y marca 'LST'
        else:
            codigo = '3'  # vendedor distinto de 'P' y otra marca

    # Buscar el límite desde la base de datos
    try:
        confi = DiscountConfig.objects.get(code=codigo)
        limite = confi.max_discount_limit
    except DiscountConfig.DoesNotExist:
        limite = 0

    descuentoMax = producto.max_store_discount if producto.max_store_discount else 0.0
    # Aquí va tu validación común
    if new_price > 0:
        descuentoMax = new_discounted_price
        return math.floor(min(descuentoMax * 100, limite))
    
    else:
        return math.floor(min(descuentoMax * 100, limite))