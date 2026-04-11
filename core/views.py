from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    HouseLoginForm,
    InitialAdminSetupForm,
    PagoForm,
    PropiedadForm,
    SoportePersonalizadoForm,
    UsuarioCasaForm,
)
from .models import Pago, PerfilUsuario, Propiedad, PropiedadImagen, SolicitudSoporte


COMMON_ISSUE_CATALOG = [
    {
        'category': SolicitudSoporte.CATEGORIA_FUGA,
        'label': 'Fuga de agua',
        'title': 'Fuga de agua en la vivienda',
        'icon': 'water_drop',
        'priority': SolicitudSoporte.PRIORIDAD_ALTA,
    },
    {
        'category': SolicitudSoporte.CATEGORIA_ELECTRICO,
        'label': 'Falla electrica',
        'title': 'Falla electrica en la vivienda',
        'icon': 'bolt',
        'priority': SolicitudSoporte.PRIORIDAD_ALTA,
    },
    {
        'category': SolicitudSoporte.CATEGORIA_HUMEDAD,
        'label': 'Humedad o filtracion',
        'title': 'Humedad o filtracion detectada',
        'icon': 'humidity_high',
        'priority': SolicitudSoporte.PRIORIDAD_MEDIA,
    },
    {
        'category': SolicitudSoporte.CATEGORIA_CERRADURA,
        'label': 'Puerta o cerradura',
        'title': 'Problema con puerta o cerradura',
        'icon': 'door_front',
        'priority': SolicitudSoporte.PRIORIDAD_MEDIA,
    },
    {
        'category': SolicitudSoporte.CATEGORIA_GAS,
        'label': 'Gas u olor extrano',
        'title': 'Revision por posible fuga de gas',
        'icon': 'mode_fan',
        'priority': SolicitudSoporte.PRIORIDAD_ALTA,
    },
    {
        'category': SolicitudSoporte.CATEGORIA_ELECTRODOMESTICO,
        'label': 'Electrodomestico',
        'title': 'Revision de electrodomestico',
        'icon': 'kitchen',
        'priority': SolicitudSoporte.PRIORIDAD_BAJA,
    },
]
COMMON_ISSUE_MAP = {issue['category']: issue for issue in COMMON_ISSUE_CATALOG}


def has_bootstrapped_users():
    return User.objects.exists()


def get_or_create_profile(user):
    defaults = {
        'rol': PerfilUsuario.ROL_ADMIN if user.is_superuser else PerfilUsuario.ROL_INQUILINO,
    }
    profile, _ = PerfilUsuario.objects.get_or_create(user=user, defaults=defaults)
    if user.is_superuser and profile.rol != PerfilUsuario.ROL_ADMIN:
        profile.rol = PerfilUsuario.ROL_ADMIN
        profile.save(update_fields=['rol'])
    return profile


def get_request_profile(request):
    if not hasattr(request, '_cached_profile'):
        request._cached_profile = get_or_create_profile(request.user)
    return request._cached_profile


def build_context(request, active_section, **extra):
    profile = get_request_profile(request)
    context = {
        'active_section': active_section,
        'is_admin': profile.es_admin,
        'user_profile': profile,
    }
    context.update(extra)
    return context


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = get_request_profile(request)
        if not profile.es_admin:
            messages.error(request, 'Esta seccion es solo para administracion.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def can_access_property(profile, propiedad):
    return profile.es_admin or profile.propiedad_id == propiedad.id


def visible_properties_for(profile):
    queryset = Propiedad.objects.prefetch_related('imagenes', 'usuarios__user').order_by('nombre')
    if profile.es_admin:
        return queryset
    if profile.propiedad_id:
        return queryset.filter(pk=profile.propiedad_id)
    return queryset.none()


def visible_payments_for(profile):
    queryset = Pago.objects.select_related('propiedad').order_by('fecha_limite')
    if profile.es_admin:
        return queryset
    if profile.propiedad_id:
        return queryset.filter(propiedad_id=profile.propiedad_id)
    return queryset.none()


def visible_support_requests_for(profile):
    queryset = SolicitudSoporte.objects.select_related('propiedad', 'reportado_por').order_by('-creado_en')
    if profile.es_admin:
        return queryset
    if profile.propiedad_id:
        return queryset.filter(propiedad_id=profile.propiedad_id)
    return queryset.none()


def setup(request):
    if has_bootstrapped_users():
        return redirect('login')

    form = InitialAdminSetupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        PerfilUsuario.objects.create(user=user, rol=PerfilUsuario.ROL_ADMIN)
        login(request, user)
        messages.success(request, 'Cuenta administradora creada. Ya puedes gestionar el sistema.')
        return redirect('dashboard')

    return render(request, 'core/setup.html', {'form': form, 'standalone': True})


def login_view(request):
    if not has_bootstrapped_users():
        return redirect('setup')
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = HouseLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        return redirect(next_url or 'dashboard')

    return render(
        request,
        'core/login.html',
        {
            'form': form,
            'standalone': True,
            'next': request.GET.get('next', ''),
        },
    )


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesion cerrada correctamente.')
    return redirect('login')


@login_required
def dashboard(request):
    profile = get_request_profile(request)
    propiedades_qs = visible_properties_for(profile)
    pagos_qs = visible_payments_for(profile)
    soporte_qs = visible_support_requests_for(profile)

    total_revenue = pagos_qs.filter(estado='PAGADO').aggregate(total=Sum('monto_mensual'))['total'] or Decimal('0.00')
    total_pending = pagos_qs.exclude(estado='PAGADO').aggregate(total=Sum('monto_mensual'))['total'] or Decimal('0.00')
    total_propiedades = propiedades_qs.count()
    total_ocupadas = propiedades_qs.filter(estado='ALQUILADA').count()
    ocupacion = round((total_ocupadas / total_propiedades) * 100, 1) if total_propiedades else 0

    context = {
        'total_revenue': total_revenue,
        'total_pending': total_pending,
        'total_propiedades': total_propiedades,
        'ocupacion': ocupacion,
        'solicitudes_abiertas_count': soporte_qs.exclude(estado=SolicitudSoporte.ESTADO_RESUELTA).count(),
        'pagos_recientes': pagos_qs.order_by('fecha_limite')[:5],
        'solicitudes_recientes': soporte_qs[:6],
        'propiedades_destacadas': propiedades_qs[:4],
    }

    if not profile.es_admin:
        propiedad = profile.propiedad
        context.update(
            {
                'propiedad_asignada': propiedad,
                'proximo_pago': pagos_qs.exclude(estado='PAGADO').order_by('fecha_limite').first() or pagos_qs.first(),
                'pagos_pendientes_count': pagos_qs.exclude(estado='PAGADO').count(),
            }
        )

    return render(request, 'core/dashboard.html', build_context(request, 'dashboard', **context))


@login_required
def pagos(request):
    profile = get_request_profile(request)
    pagos_list = visible_payments_for(profile)
    total_revenue = pagos_list.filter(estado='PAGADO').aggregate(total=Sum('monto_mensual'))['total'] or Decimal('0.00')
    total_outstanding = pagos_list.filter(estado='ATRASADO').aggregate(total=Sum('monto_mensual'))['total'] or Decimal('0.00')
    total_upcoming = pagos_list.filter(estado='PENDIENTE').aggregate(total=Sum('monto_mensual'))['total'] or Decimal('0.00')

    return render(
        request,
        'core/pagos.html',
        build_context(
            request,
            'pagos',
            pagos_list=pagos_list,
            total_revenue=total_revenue,
            total_outstanding=total_outstanding,
            total_upcoming=total_upcoming,
        ),
    )


@login_required
def soporte(request):
    profile = get_request_profile(request)
    propiedades_soporte = visible_properties_for(profile).prefetch_related(
        Prefetch('usuarios', queryset=PerfilUsuario.objects.select_related('user').order_by('user__username')),
        Prefetch('solicitudes_soporte', queryset=SolicitudSoporte.objects.select_related('reportado_por').order_by('-creado_en')),
    )
    incidencias = visible_support_requests_for(profile)

    return render(
        request,
        'core/soporte.html',
        build_context(
            request,
            'soporte',
            propiedades_soporte=propiedades_soporte,
            incidencias=incidencias[:12],
            common_issue_catalog=COMMON_ISSUE_CATALOG,
            priority_choices=SolicitudSoporte.PRIORIDADES,
            open_incidents_count=incidencias.exclude(estado=SolicitudSoporte.ESTADO_RESUELTA).count(),
            resolved_incidents_count=incidencias.filter(estado=SolicitudSoporte.ESTADO_RESUELTA).count(),
            custom_support_form=SoportePersonalizadoForm(),
        ),
    )


@login_required
@require_POST
def soporte_crear_rapido(request):
    profile = get_request_profile(request)
    propiedad = get_object_or_404(Propiedad, pk=request.POST.get('propiedad_id'))
    issue = COMMON_ISSUE_MAP.get(request.POST.get('categoria'))

    if not can_access_property(profile, propiedad):
        messages.error(request, 'No puedes reportar incidencias para otra vivienda.')
        return redirect('soporte')

    if issue is None:
        messages.error(request, 'La categoria seleccionada no es valida.')
        return redirect('soporte')

    SolicitudSoporte.objects.create(
        propiedad=propiedad,
        reportado_por=request.user,
        categoria=issue['category'],
        titulo=issue['title'],
        prioridad=issue['priority'],
    )
    messages.success(request, 'Incidencia registrada correctamente.')
    return redirect('soporte')


@login_required
@require_POST
def soporte_crear_personalizado(request):
    profile = get_request_profile(request)
    form = SoportePersonalizadoForm(request.POST)

    if not form.is_valid():
        error = next(iter(form.errors.values()))[0]
        messages.error(request, error)
        return redirect('soporte')

    propiedad = get_object_or_404(Propiedad, pk=form.cleaned_data['propiedad_id'])
    if not can_access_property(profile, propiedad):
        messages.error(request, 'No puedes reportar incidencias para otra vivienda.')
        return redirect('soporte')

    SolicitudSoporte.objects.create(
        propiedad=propiedad,
        reportado_por=request.user,
        categoria=SolicitudSoporte.CATEGORIA_OTRO,
        titulo=form.cleaned_data['titulo'],
        descripcion=form.cleaned_data['descripcion'],
        prioridad=form.cleaned_data['prioridad'],
    )
    messages.success(request, 'Dano personalizado registrado correctamente.')
    return redirect('soporte')


@admin_required
@require_POST
def soporte_actualizar_estado(request, pk):
    incidencia = get_object_or_404(SolicitudSoporte, pk=pk)
    estado = request.POST.get('estado')
    estados_validos = {choice[0] for choice in SolicitudSoporte.ESTADOS}

    if estado not in estados_validos:
        messages.error(request, 'El estado seleccionado no es valido.')
        return redirect('soporte')

    incidencia.estado = estado
    incidencia.save(update_fields=['estado', 'actualizado_en'])
    messages.success(request, 'Estado de la incidencia actualizado.')
    return redirect('soporte')


@login_required
def propiedades(request):
    profile = get_request_profile(request)
    search_query = request.GET.get('q', '').strip()
    propiedades_list = visible_properties_for(profile)

    if search_query:
        propiedades_list = propiedades_list.filter(
            Q(nombre__icontains=search_query)
            | Q(direccion__icontains=search_query)
            | Q(inquilino_nombre__icontains=search_query)
            | Q(estado__icontains=search_query)
            | Q(usuarios__user__username__icontains=search_query)
            | Q(usuarios__user__first_name__icontains=search_query)
            | Q(usuarios__user__last_name__icontains=search_query)
        ).distinct()

    return render(
        request,
        'core/propiedades.html',
        build_context(
            request,
            'propiedades',
            propiedades_list=propiedades_list,
            search_query=search_query,
            total_propiedades=propiedades_list.count(),
        ),
    )


@admin_required
def usuarios(request):
    form = UsuarioCasaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        perfil = form.save()
        messages.success(request, f'Usuario {perfil.user.username} creado correctamente.')
        return redirect('usuarios')

    perfiles = PerfilUsuario.objects.select_related('user', 'propiedad').order_by('rol', 'user__username')

    return render(
        request,
        'core/usuarios.html',
        build_context(
            request,
            'usuarios',
            form=form,
            perfiles=perfiles,
            total_usuarios=perfiles.count(),
            total_admins=perfiles.filter(rol=PerfilUsuario.ROL_ADMIN).count(),
            total_inquilinos=perfiles.filter(rol=PerfilUsuario.ROL_INQUILINO).count(),
        ),
    )


def guardar_imagenes_propiedad(propiedad, imagenes):
    for imagen in imagenes:
        PropiedadImagen.objects.create(propiedad=propiedad, imagen=imagen)


@admin_required
def propiedad_crear(request):
    form = PropiedadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        propiedad = form.save()
        guardar_imagenes_propiedad(propiedad, form.cleaned_data.get('imagenes', []))
        messages.success(request, 'Propiedad creada correctamente.')
        return redirect('propiedades')

    return render(
        request,
        'core/propiedad_form.html',
        build_context(
            request,
            'propiedades',
            form=form,
            titulo='Anadir propiedad',
            imagenes_existentes=[],
            imagen_externa_actual=None,
        ),
    )


@admin_required
def propiedad_editar(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    form = PropiedadForm(request.POST or None, request.FILES or None, instance=propiedad)
    if request.method == 'POST' and form.is_valid():
        propiedad = form.save()
        guardar_imagenes_propiedad(propiedad, form.cleaned_data.get('imagenes', []))
        messages.success(request, 'Propiedad actualizada correctamente.')
        return redirect('propiedades')

    return render(
        request,
        'core/propiedad_form.html',
        build_context(
            request,
            'propiedades',
            form=form,
            titulo='Editar propiedad',
            imagenes_existentes=propiedad.imagenes.all(),
            imagen_externa_actual=propiedad.imagen_url,
        ),
    )


@admin_required
def pago_crear(request):
    form = PagoForm(
        request.POST or None,
        propiedad_queryset=Propiedad.objects.order_by('nombre'),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pago registrado correctamente.')
        return redirect('pagos')

    return render(
        request,
        'core/pago_form.html',
        build_context(request, 'pagos', form=form, titulo='Registrar pago'),
    )


@admin_required
def pago_editar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    form = PagoForm(
        request.POST or None,
        instance=pago,
        propiedad_queryset=Propiedad.objects.order_by('nombre'),
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pago actualizado correctamente.')
        return redirect('pagos')

    return render(
        request,
        'core/pago_form.html',
        build_context(request, 'pagos', form=form, titulo='Editar pago'),
    )
