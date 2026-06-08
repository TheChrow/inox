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
from adapters.odoo.service.odoo_service_partner import PartnerOdooService
from adapters.odoo.service.odoo_service_sales import SaleOdooService
from domain.cotizacion_pdf_service import CotizacionNotFoundError, CotizacionPDFService
from domain.customer_service import CustomerService
from infrastructure.models.config_discount_db import DiscountConfig
from infrastructure.models.products_db import Product
from infrastructure.models.seller_db import Seller
from presentation.serializers.partner_serializers import (
    CreatePartnerRequestSerializer,
    UpdatePartnerRequestSerializer,
)
from presentation.serializers.sale_serializers import (
    CreateQuotationRequestSerializer,
    ListQuotationsRequestSerializer,
    UpdateQuotationRequestSerializer,
)


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


@login_required
def generate_quote(request, odoo_name: str | None = None):
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
        'odoo_name': odoo_name,
        'username': username,
        'regiones': regiones,
        'sucursal': sucurs,
        'nombreuser': nombreUser,
        'codigoVendedor': codVen
    }

    return render(request, 'quotation.html', context)
    
@login_required
def list_of_quotes(request):
    username = request.user.username
    name_user = request.user.first_name

    try:
        seller = Seller.objects.get(auth_user=request.user)
    except Seller.DoesNotExist:
        return JsonResponse(
            {'error': 'No se encontró el vendedor relacionado con el usuario autenticado'},
            status=404,
        )

    user_groups = list(request.user.groups.values_list('name', flat=True))

    context = {
        'username': username,
        'nameUser': name_user,
        'codigoVendedor': seller.code,
        'nombreVendedor': seller.auth_user.get_full_name() or username,
        'user_groups': user_groups,
    }
    return render(request, 'lista_cotizaciones.html', context)

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


class OdooPartnerCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreatePartnerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = CustomerService(PartnerOdooService(get_odoo_client()))
        try:
            result = service.create_or_update(
                customer=data["customer"],
                contacts=data.get("contacts"),
            )
        except Exception as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        http_status = status.HTTP_200_OK if result["existing"] else status.HTTP_201_CREATED
        return Response({"ok": True, **result}, status=http_status)


class OdooPartnerSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < 2:
            return Response({"ok": True, "records": []}, status=status.HTTP_200_OK)

        try:
            limit = int(request.query_params.get("limit") or 10)
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 25))

        service = PartnerOdooService(get_odoo_client())
        try:
            records = service.search_customers(query, limit=limit)
        except Exception as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"ok": True, "records": records}, status=status.HTTP_200_OK)


class OdooPartnerReadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id: int):
        service = PartnerOdooService(get_odoo_client())
        try:
            data = service.read_customer_full(customer_id)
        except Exception as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not data:
            return Response(
                {"ok": False, "error": "Cliente no encontrado en Odoo"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Solo el primer contacto si existe. La dirección viaja en customer.
        first_contact = (data.get("contacts") or [None])[0]
        return Response(
            {
                "ok": True,
                "customer": data["customer"],
                "contact": first_contact,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, customer_id: int):
        serializer = UpdatePartnerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = CustomerService(PartnerOdooService(get_odoo_client()))
        try:
            result = service.update_existing(
                customer_id=customer_id,
                customer=data["customer"],
                contact=data.get("contact"),
            )
        except ValueError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ok": True, **result}, status=status.HTTP_200_OK)


class OdooQuotationListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ListQuotationsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        page = data.get("page", 1)
        page_size = data.get("page_size", 20)
        offset = (page - 1) * page_size

        date_from = data.get("date_from")
        date_to = data.get("date_to")
        date_doc = data.get("date_doc")

        service = SaleOdooService(get_odoo_client())
        try:
            result = service.list_quotations(
                limit=page_size,
                offset=offset,
                date_from=date_from.isoformat() if date_from else None,
                date_to=date_to.isoformat() if date_to else None,
                date_doc=date_doc.isoformat() if date_doc else None,
                doc_num=(data.get("doc_num") or "").strip() or None,
                partner_text=(data.get("partner_text") or "").strip() or None,
                salesperson_id=data.get("salesperson_id"),
                salesperson_name=(data.get("salesperson_name") or "").strip() or None,
                state=(data.get("state") or "").strip() or None,
                amount_total=data.get("amount_total"),
            )
        except Exception as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        total = result["total"]
        total_pages = math.ceil(total / page_size) if page_size else 1

        return Response(
            {
                "ok": True,
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "records": result["records"],
            },
            status=status.HTTP_200_OK,
        )


class OdooQuotationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, odoo_name: str):
        service = SaleOdooService(get_odoo_client())
        try:
            data = service.read_quotation_by_name(odoo_name)
        except Exception as exc:
            return Response(
                {"ok": False, "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not data:
            return Response(
                {"ok": False, "error": "Cotización no encontrada en Odoo"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"ok": True, **data}, status=status.HTTP_200_OK)

    def put(self, request, odoo_name: str):
        serializer = UpdateQuotationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        validity_date = data.get("validity_date")

        service = SaleOdooService(get_odoo_client())
        try:
            result = service.update_quotation(
                name=odoo_name,
                lines=data["lines"],
                partner_id=data.get("partner_id"),
                validity_date=validity_date.isoformat() if validity_date else None,
                client_order_ref=data.get("client_order_ref"),
                note=data.get("note"),
                salesperson_code=(data.get("salesperson_code") or "").strip() or None,
            )
        except ValueError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ok": True, **result}, status=status.HTTP_200_OK)


class OdooQuotationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateQuotationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        validity_date = data.get("validity_date")

        service = SaleOdooService(get_odoo_client())
        try:
            result = service.create_quotation(
                partner_id=data["partner_id"],
                lines=data["lines"],
                validity_date=validity_date.isoformat() if validity_date else None,
                client_order_ref=data.get("client_order_ref"),
                note=data.get("note"),
                salesperson_code=(data.get("salesperson_code") or "").strip() or None,
            )
        except ValueError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"ok": True, **result}, status=status.HTTP_201_CREATED)


class OdooQuotationPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, odoo_name: str):
        client = get_odoo_client()
        service = CotizacionPDFService(
            sale_service=SaleOdooService(client),
            partner_service=PartnerOdooService(client),
        )
        vendedor = _vendedor_para_pdf(request.user)
        try:
            pdf_bytes = service.generar_pdf(
                odoo_name,
                vendedor=vendedor,
                base_url=request.build_absolute_uri("/"),
            )
        except CotizacionNotFoundError as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            return Response({"ok": False, "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="cotizacion_{odoo_name}.pdf"'
        return response


def _vendedor_para_pdf(user) -> dict:
    try:
        seller = Seller.objects.select_related("auth_user", "branch").get(auth_user=user)
    except Seller.DoesNotExist:
        return {"nombre": user.get_full_name() or user.username, "email": user.email}
    auth = seller.auth_user
    return {
        "nombre": (auth.get_full_name() or auth.username).strip(),
        "email": auth.email or "",
        "telefono": "",
        "sucursal": seller.branch.name if seller.branch_id else "",
        "codigo": seller.code,
    }


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