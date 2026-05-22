from django.contrib.auth.models import AnonymousUser

def user_groups(request):
    if isinstance(request.user, AnonymousUser):
        return {'user_groups': []}
    user_groups = list(request.user.groups.values_list('name', flat=True))
    return {'user_groups': user_groups}

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
