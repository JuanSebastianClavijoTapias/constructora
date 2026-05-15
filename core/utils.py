"""
Funciones auxiliares y utilidades del módulo core.
Decoradores, funciones de contexto y otras utilidades comunes.
"""

from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import PerfilUsuario, Propiedad


def get_or_create_profile(user):
    """Obtener o crear perfil del usuario."""
    defaults = {
        'rol': PerfilUsuario.ROL_ADMIN if user.is_superuser else PerfilUsuario.ROL_INQUILINO,
    }
    profile, _ = PerfilUsuario.objects.get_or_create(user=user, defaults=defaults)
    if user.is_superuser and profile.rol != PerfilUsuario.ROL_ADMIN:
        profile.rol = PerfilUsuario.ROL_ADMIN
        profile.save(update_fields=['rol'])
    return profile


def get_request_profile(request):
    """Obtener perfil del usuario actual de la request."""
    if not hasattr(request, '_cached_profile'):
        request._cached_profile = get_or_create_profile(request.user)
    return request._cached_profile


def admin_required(view_func):
    """Decorador que requiere permisos de admin para acceder a contabilidad."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = get_request_profile(request)
        
        # Verificar que es administrador
        if not profile.es_admin:
            messages.error(request, 'Acceso denegado: Esta sección es solo para administración.')
            return redirect('dashboard')
        
        # Verificar acceso a propiedad si está en los parámetros
        propiedad_id = kwargs.get('propiedad_id')
        if propiedad_id:
            try:
                propiedad = Propiedad.objects.get(pk=propiedad_id)
                if not can_access_property(profile, propiedad):
                    messages.error(request, 'No tienes permiso para acceder a esta propiedad.')
                    return redirect('dashboard')
            except Propiedad.DoesNotExist:
                messages.error(request, 'La propiedad no existe.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)

    return wrapper


def contabilidad_required(view_func):
    """
    Decorador estricto para módulo de contabilidad.
    Solo permite acceso a administradores verificados.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = get_request_profile(request)
        
        # Verificación stricta: debe ser administrador
        if not profile.es_admin or not request.user.is_active:
            messages.error(request, 'Acceso denegado: No autorizado para acceder a contabilidad.')
            return redirect('dashboard')
        
        # Log de acceso a función sensible
        import logging
        logger = logging.getLogger('contabilidad')
        logger.info(f'Acceso a contabilidad: {request.user.username} - {request.path}')
        
        return view_func(request, *args, **kwargs)

    return wrapper


def can_access_property(profile, propiedad):
    """Verificar si el perfil puede acceder a una propiedad."""
    return profile.es_admin or profile.propiedad_id == propiedad.id


def visible_properties_for(profile):
    """Obtener propiedades visibles para un perfil."""
    queryset = Propiedad.objects.prefetch_related('imagenes', 'usuarios__user').order_by('nombre')
    if not profile.es_admin:
        # Los inquilinos solo ven su propiedad
        queryset = queryset.filter(id=profile.propiedad_id)
    return queryset


def build_context(request, active_section, **extra):
    """Construir contexto común para templates."""
    profile = get_request_profile(request)
    context = {
        'active_section': active_section,
        'is_admin': profile.es_admin,
        'user_profile': profile,
    }
    context.update(extra)
    return context
