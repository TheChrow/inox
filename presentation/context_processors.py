from django.contrib.auth.models import AnonymousUser
from django.db.models import Prefetch

from infrastructure.models.menu_module_db import MenuModule
from infrastructure.models.nav_item_db import NavItem


def user_groups(request):
    if isinstance(request.user, AnonymousUser):
        return {'user_groups': []}
    user_groups = list(request.user.groups.values_list('name', flat=True))
    return {'user_groups': user_groups}


def menu_modules(request):
    if isinstance(request.user, AnonymousUser):
        return {'menu_modules': MenuModule.objects.none()}

    modules = (
        MenuModule.objects
        .filter(is_active=True, groups__in=request.user.groups.all())
        .distinct()
        .order_by('order', 'label')
    )
    return {'menu_modules': modules}


def nav_items(request):
    if isinstance(request.user, AnonymousUser):
        return {'nav_items': NavItem.objects.none()}

    user_groups_qs = request.user.groups.all()
    visible_children = (
        NavItem.objects
        .filter(is_active=True, groups__in=user_groups_qs)
        .distinct()
        .order_by('order', 'label')
    )
    items = (
        NavItem.objects
        .filter(is_active=True, groups__in=user_groups_qs, parent__isnull=True)
        .distinct()
        .order_by('order', 'label')
        .prefetch_related(
            Prefetch('children', queryset=visible_children, to_attr='visible_children')
        )
    )
    return {'nav_items': items}

def current_user(request):
    if isinstance(request.user, AnonymousUser):
        return {'current_user': None}
    
    return {'current_user': request.user}

def salesperson_code(request):
    if request.user.is_authenticated:
        user_db = getattr(request.user, 'usuariodb', None)  # Relación con UsuarioDB
        
        # Obtener nombre del vendedor
        vendedor_nombre = user_db.vendedor.nombre if user_db and hasattr(user_db, 'vendedor') else None
        vendedor_codigo = user_db.vendedor.codigo if user_db and hasattr(user_db, 'vendedor') else None

        # Obtener showroom del usuario
        showroom = user_db.sucursal.nombre if user_db and hasattr(user_db, 'sucursal') else "No asignado"

        return {
            'vendedor_nombre': vendedor_nombre,
            'codigo_vendedor': vendedor_codigo,
            'showroom': showroom
        }

    return {'vendedor_nombre': None, 'codigo_vendedor': None, 'showroom': "No asignado"}
