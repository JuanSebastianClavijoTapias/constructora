from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Propiedad, Pago, PropiedadImagen
from .forms import PropiedadForm, PagoForm

def dashboard(request):
    return render(request, 'core/dashboard.html')

def pagos(request):
    pagos_list = Pago.objects.all().order_by('fecha_limite')
    
    # Calculate some stats for the header
    total_revenue = sum(p.monto_mensual for p in pagos_list if p.estado == 'PAGADO')
    total_outstanding = sum(p.monto_mensual for p in pagos_list if p.estado == 'ATRASADO')
    total_upcoming = sum(p.monto_mensual for p in pagos_list if p.estado == 'PENDIENTE')
    
    context = {
        'pagos_list': pagos_list,
        'total_revenue': total_revenue,
        'total_outstanding': total_outstanding,
        'total_upcoming': total_upcoming,
    }
    return render(request, 'core/pagos.html', context)

def soporte(request):
    return render(request, 'core/soporte.html')


def propiedades(request):
    search_query = request.GET.get('q', '').strip()
    propiedades_list = Propiedad.objects.all().prefetch_related('imagenes').order_by('nombre')

    if search_query:
        propiedades_list = propiedades_list.filter(
            Q(nombre__icontains=search_query)
            | Q(direccion__icontains=search_query)
            | Q(inquilino_nombre__icontains=search_query)
            | Q(estado__icontains=search_query)
        ).distinct()

    context = {
        'propiedades_list': propiedades_list,
        'search_query': search_query,
        'total_propiedades': propiedades_list.count(),
    }
    return render(request, 'core/propiedades.html', context)


def guardar_imagenes_propiedad(propiedad, imagenes):
    for imagen in imagenes:
        PropiedadImagen.objects.create(propiedad=propiedad, imagen=imagen)


# --- CRUD Propiedades ---
def propiedad_crear(request):
    if request.method == 'POST':
        form = PropiedadForm(request.POST, request.FILES)
        if form.is_valid():
            propiedad = form.save()
            guardar_imagenes_propiedad(propiedad, form.cleaned_data.get('imagenes', []))
            return redirect('propiedades')
    else:
        form = PropiedadForm()
    return render(
        request,
        'core/propiedad_form.html',
        {
            'form': form,
            'titulo': 'Añadir Propiedad',
            'imagenes_existentes': [],
            'imagen_externa_actual': None,
        },
    )

def propiedad_editar(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    if request.method == 'POST':
        form = PropiedadForm(request.POST, request.FILES, instance=propiedad)
        if form.is_valid():
            propiedad = form.save()
            guardar_imagenes_propiedad(propiedad, form.cleaned_data.get('imagenes', []))
            return redirect('propiedades')
    else:
        form = PropiedadForm(instance=propiedad)
    return render(
        request,
        'core/propiedad_form.html',
        {
            'form': form,
            'titulo': 'Editar Propiedad',
            'imagenes_existentes': propiedad.imagenes.all(),
            'imagen_externa_actual': propiedad.imagen_url,
        },
    )

# --- CRUD Pagos ---
def pago_crear(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pagos')
    else:
        form = PagoForm()
    return render(request, 'core/pago_form.html', {'form': form, 'titulo': 'Registrar Pago'})

def pago_editar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    if request.method == 'POST':
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            return redirect('pagos')
    else:
        form = PagoForm(instance=pago)
    return render(request, 'core/pago_form.html', {'form': form, 'titulo': 'Modificar Pago'})
