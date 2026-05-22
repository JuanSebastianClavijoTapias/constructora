"""
Vistas para el módulo de contabilidad y finanzas de propiedades.
Gestiona nómina, impuestos, obligaciones, servicios y reportes.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    PersonalEmpleadoForm,
    NominaEmpleadoForm,
    EquiposUniformesForm,
    ObligacionFiscalForm,
    PagoObligacionForm,
    ContratoMantenimientoForm,
    PagoMantenimientoForm,
    GastoServicioPublicoForm,
)
from .models import (
    Propiedad,
    PersonalEmpleado,
    NominaEmpleado,
    EquiposUniformes,
    ObligacionFiscal,
    PagoObligacion,
    ContratoMantenimiento,
    PagoMantenimiento,
    GastoServicioPublico,
    ReporteContableMensual,
)
from .utils import admin_required, contabilidad_required, build_context, get_request_profile, visible_properties_for, can_access_property
from .accounting import GeneradorReportesContables, CalculadoraNomina, AnalizadorTendenciasFinancieras
from .export_utils import exportar_nominas_excel, exportar_obligaciones_excel, ExportadorPDF


# ========== DASHBOARD DE CONTABILIDAD ==========

@admin_required
def contabilidad_dashboard(request):
    """Panel principal de contabilidad con resumen de gastos y alertas."""
    profile = get_request_profile(request)
    propiedades = visible_properties_for(profile)
    
    # Obtener mes actual
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    
    # Resumen consolidado de todas las propiedades
    total_gastos_mes = Decimal('0')
    total_nómina = Decimal('0')
    total_mantenimiento = Decimal('0')
    total_servicios = Decimal('0')
    
    reportes = ReporteContableMensual.objects.filter(
        propiedad__in=propiedades,
        periodo_mes=inicio_mes
    )
    
    for reporte in reportes:
        total_gastos_mes += reporte.total_gastos_operacionales
        total_nómina += reporte.subtotal_personal
        total_mantenimiento += reporte.total_mantenimiento
        total_servicios += reporte.total_servicios_publicos
    
    # Alertas de obligaciones fiscales vencidas
    alertas = []
    for propiedad in propiedades:
        alertas.extend(AnalizadorTendenciasFinancieras.alertas_incumplimiento_fiscal(propiedad))
    
    # Próximos vencimientos de obligaciones
    proximos_vencimientos = ObligacionFiscal.objects.filter(
        propiedad__in=propiedades,
        activa=True,
        fecha_vencimiento_proximo__gte=hoy,
        fecha_vencimiento_proximo__lte=hoy + timedelta(days=30)
    ).order_by('fecha_vencimiento_proximo')[:5]
    
    # Contratos próximos a renovarse
    contratos_renovacion = ContratoMantenimiento.objects.filter(
        propiedad__in=propiedades,
        estado='ACTIVO'
    ).exclude(fecha_fin__isnull=True)
    
    contratos_alerta = [c for c in contratos_renovacion if c.requiere_renovacion][:5]
    
    # Nóminas del mes actual - estado de pago
    nominas_mes = NominaEmpleado.objects.filter(
        periodo_mes__year=hoy.year,
        periodo_mes__month=hoy.month,
        empleado__propiedad__in=propiedades
    ) | NominaEmpleado.objects.filter(
        periodo_mes__year=hoy.year,
        periodo_mes__month=hoy.month,
        empleado__propiedad__isnull=True
    )
    
    nominas_pagadas = nominas_mes.filter(estado='PAGADA').count()
    nominas_pendientes = nominas_mes.exclude(estado='PAGADA').count()
    total_nominas_mes = nominas_mes.count()
    
    # Calcular total de nóminas del mes actual
    total_nomina_actual = nominas_mes.aggregate(total=Sum('total_neto'))['total'] or Decimal('0')
    
    # Total de empleados activos
    empleados_activos = PersonalEmpleado.objects.filter(activo=True)
    
    context = build_context(
        request,
        'contabilidad',
        total_gastos_mes=total_gastos_mes,
        total_nómina=total_nomina_actual,
        total_mantenimiento=total_mantenimiento,
        total_servicios=total_servicios,
        alertas=alertas,
        proximos_vencimientos=proximos_vencimientos,
        contratos_alerta=contratos_alerta,
        fecha_reporte=inicio_mes,
        nominas_pagadas=nominas_pagadas,
        nominas_pendientes=nominas_pendientes,
        total_nominas_mes=total_nominas_mes,
        empleados_activos=empleados_activos,
    )
    
    return render(request, 'core/contabilidad/dashboard.html', context)


# ========== GESTIÓN DE EMPLEADOS ==========

@admin_required
def empleados_lista(request, propiedad_id=None):
    """Lista todos los empleados o empleados de una propiedad específica."""
    profile = get_request_profile(request)
    
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
        empleados = PersonalEmpleado.objects.filter(propiedad=propiedad).order_by('tipo_empleado', 'nombre_completo')
    else:
        propiedades = visible_properties_for(profile)
        # Incluir todos los empleados: con propiedad asignada O sin propiedad (NULL)
        empleados = PersonalEmpleado.objects.filter(
            Q(propiedad__in=propiedades) | Q(propiedad__isnull=True)
        ).order_by('propiedad', 'tipo_empleado')
    
    empleados_activos = empleados.filter(activo=True)
    empleados_inactivos = empleados.filter(activo=False)
    
    context = build_context(
        request,
        'contabilidad',
        empleados_activos=empleados_activos,
        empleados_inactivos=empleados_inactivos,
        total_empleados=empleados.count(),
        propiedad_id=propiedad_id,
    )
    
    return render(request, 'core/contabilidad/empleados_lista.html', context)


@admin_required
def empleado_crear(request, propiedad_id=None):
    """Crear nuevo empleado."""
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    else:
        propiedad = None
    
    form = PersonalEmpleadoForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        empleado = form.save(commit=False)
        if propiedad:
            empleado.propiedad = propiedad
        empleado.save()
        messages.success(request, f'Empleado {empleado.nombre_completo} creado exitosamente.')
        return redirect('empleados_lista') if not propiedad_id else redirect('empleados_lista', propiedad_id=propiedad_id)
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        titulo='Agregar Empleado',
        propiedad=propiedad,
    )
    
    return render(request, 'core/contabilidad/empleado_form.html', context)


@admin_required
def empleado_editar(request, pk):
    """Editar empleado existente."""
    empleado = get_object_or_404(PersonalEmpleado, pk=pk)
    form = PersonalEmpleadoForm(request.POST or None, instance=empleado)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Empleado {empleado.nombre_completo} actualizado correctamente.')
        return redirect('empleados_lista')
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        empleado=empleado,
        titulo=f'Editar {empleado.nombre_completo}',
    )
    
    return render(request, 'core/contabilidad/empleado_form.html', context)


@admin_required
def empleado_detalle(request, pk):
    """Ver detalles del empleado incluyendo su historial de nómina."""
    empleado = get_object_or_404(PersonalEmpleado, pk=pk)
    nominas = NominaEmpleado.objects.filter(empleado=empleado).order_by('-periodo_mes')
    equipos = EquiposUniformes.objects.filter(empleado=empleado).order_by('-fecha_asignacion')
    
    # Estadísticas
    total_pagado = nominas.aggregate(Sum('total_neto'))['total_neto__sum'] or Decimal('0')
    
    # Cálculos de prestaciones e impuestos 2026
    salario_base = empleado.salario_mensual_base
    smmlv_2026 = Decimal('1830000')
    
    # Prestaciones anuales
    prima_semestral = salario_base / 2
    vacaciones_anuales = salario_base
    cesantias_anuales = salario_base
    total_prestaciones_anuales = (salario_base * 12) + prima_semestral + vacaciones_anuales + cesantias_anuales
    
    # Impuestos y aportes 2026
    aportes_sena = salario_base * Decimal('0.005')  # 0.5%
    icbf = salario_base * Decimal('0.03')  # 3%
    arl_promedio = salario_base * Decimal('0.005')  # 0.5% promedio
    pensión = salario_base * Decimal('0.04')  # 4%
    total_descuentos = aportes_sena + icbf + arl_promedio + pensión  # 8%
    
    context = build_context(
        request,
        'contabilidad',
        empleado=empleado,
        nominas=nominas,
        equipos=equipos,
        total_pagado=total_pagado,
        smmlv_2026=smmlv_2026,
        prima_semestral=prima_semestral,
        vacaciones_anuales=vacaciones_anuales,
        cesantias_anuales=cesantias_anuales,
        total_prestaciones_anuales=total_prestaciones_anuales,
        aportes_sena=aportes_sena,
        icbf=icbf,
        arl_promedio=arl_promedio,
        pensión=pensión,
        total_descuentos=total_descuentos,
    )
    
    return render(request, 'core/contabilidad/empleado_detalle.html', context)


# ========== GESTIÓN DE NÓMINA ==========

@admin_required
def nomina_lista(request, propiedad_id=None):
    """Lista de nóminas por período."""
    profile = get_request_profile(request)
    
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
        nominas = NominaEmpleado.objects.filter(
            empleado__propiedad=propiedad
        ).order_by('-periodo_mes')
    else:
        propiedades = visible_properties_for(profile)
        # Incluir nóminas de empleados con propiedad asignada O sin propiedad (NULL)
        nominas = NominaEmpleado.objects.filter(
            Q(empleado__propiedad__in=propiedades) | Q(empleado__propiedad__isnull=True)
        ).order_by('-periodo_mes')
    
    # Agrupar por mes
    meses = {}
    for nomina in nominas:
        mes_key = nomina.periodo_mes.strftime('%B %Y')
        if mes_key not in meses:
            meses[mes_key] = {
                'fecha': nomina.periodo_mes,
                'nominas': [],
                'total_neto': Decimal('0'),
                'total_patronal': Decimal('0'),
            }
        meses[mes_key]['nominas'].append(nomina)
        meses[mes_key]['total_neto'] += nomina.total_neto
        meses[mes_key]['total_patronal'] += nomina.total_aportes_patronales
    
    context = build_context(
        request,
        'contabilidad',
        meses=meses,
        propiedad_id=propiedad_id,
    )
    
    return render(request, 'core/contabilidad/nomina_lista.html', context)


@admin_required
def nomina_crear(request, empleado_id, propiedad_id=None):
    """Crear nueva nómina para un empleado."""
    empleado = get_object_or_404(PersonalEmpleado, pk=empleado_id)
    
    form = NominaEmpleadoForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        nomina = form.save(commit=False)
        nomina.empleado = empleado
        
        # Calculador de nómina
        calculador = CalculadoraNomina()
        nomina = calculador.calcular_nomina_completa(nomina)
        
        nomina.save()
        messages.success(request, f'Nómina {nomina.periodo_mes.strftime("%B %Y")} creada.')
        return redirect('empleado_detalle', pk=empleado_id)
    
    # Pre-llenar con datos del empleado
    if not request.POST:
        form.initial = {
            'salario_base': empleado.salario_mensual_base,
            'periodo_mes': date.today().replace(day=1),
        }
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        empleado=empleado,
        titulo=f'Crear Nómina - {empleado.nombre_completo}',
    )
    
    return render(request, 'core/contabilidad/nomina_form.html', context)


@admin_required
def nomina_detalle(request, pk):
    """Ver detalles completos de una nómina."""
    nomina = get_object_or_404(NominaEmpleado, pk=pk)
    
    context = build_context(
        request,
        'contabilidad',
        nomina=nomina,
        aporte_arl=nomina.aporte_arl,
    )
    
    return render(request, 'core/contabilidad/nomina_detalle.html', context)


@admin_required
@require_POST
def nomina_pagar(request, pk):
    """Marcar una nómina como pagada."""
    nomina = get_object_or_404(NominaEmpleado, pk=pk)
    
    if nomina.estado != 'PAGADA':
        nomina.estado = 'PAGADA'
        nomina.fecha_pago = date.today()
        nomina.save()
        messages.success(request, f'Nómina de {nomina.empleado.nombre_completo} ({nomina.periodo_mes.strftime("%B %Y")}) marcada como pagada.')
    else:
        messages.info(request, 'Esta nómina ya fue pagada.')
    
    return redirect('nomina_detalle', pk=pk)


# ========== GESTIÓN DE OBLIGACIONES FISCALES ==========

@admin_required
def obligaciones_fiscales_lista(request, propiedad_id=None):
    """Lista de obligaciones fiscales con estado de vencimientos."""
    profile = get_request_profile(request)
    hoy = date.today()
    
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
        obligaciones = ObligacionFiscal.objects.filter(propiedad=propiedad)
    else:
        propiedades = visible_properties_for(profile)
        obligaciones = ObligacionFiscal.objects.filter(propiedad__in=propiedades)
    
    # Clasificar por estado
    vencidas = obligaciones.filter(fecha_vencimiento_proximo__lt=hoy)
    proximo_mes = obligaciones.filter(
        fecha_vencimiento_proximo__gte=hoy,
        fecha_vencimiento_proximo__lte=hoy + timedelta(days=30)
    )
    activas = obligaciones.filter(fecha_vencimiento_proximo__gt=hoy + timedelta(days=30))
    inactivas = obligaciones.filter(activa=False)
    
    total_obligaciones_vencidas = vencidas.aggregate(Sum('monto_obligacion'))['monto_obligacion__sum'] or Decimal('0')
    total_proximo_mes = proximo_mes.aggregate(Sum('monto_obligacion'))['monto_obligacion__sum'] or Decimal('0')
    
    context = build_context(
        request,
        'contabilidad',
        vencidas=vencidas,
        proximo_mes=proximo_mes,
        activas=activas,
        inactivas=inactivas,
        total_vencidas=total_obligaciones_vencidas,
        total_proximo_mes=total_proximo_mes,
        propiedad_id=propiedad_id,
    )
    
    return render(request, 'core/contabilidad/obligaciones_lista.html', context)


@admin_required
def obligacion_crear(request, propiedad_id=None):
    """Crear nueva obligación fiscal."""
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    else:
        propiedad = None
    
    form = ObligacionFiscalForm(
        request.POST or None,
        user=request.user,
        propiedad=propiedad
    )
    
    if request.method == 'POST' and form.is_valid():
        obligacion = form.save(commit=False)
        if propiedad and not obligacion.propiedad:
            obligacion.propiedad = propiedad
        obligacion.save()
        messages.success(request, 'Obligación fiscal creada.')
        return redirect('obligaciones_fiscales_lista', propiedad_id=propiedad_id) if propiedad_id else redirect('obligaciones_fiscales_lista')
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        propiedad=propiedad,
        titulo='Nueva Obligación Fiscal',
    )
    
    return render(request, 'core/contabilidad/obligacion_form.html', context)


@admin_required
def obligacion_editar(request, pk):
    """Editar obligación fiscal."""
    obligacion = get_object_or_404(ObligacionFiscal, pk=pk)
    form = ObligacionFiscalForm(
        request.POST or None,
        instance=obligacion,
        user=request.user,
        propiedad=obligacion.propiedad
    )
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Obligación actualizada.')
        return redirect('obligaciones_fiscales_lista', propiedad_id=obligacion.propiedad.id)
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        obligacion=obligacion,
        titulo=f'Editar - {obligacion.get_tipo_obligacion_display()}',
    )
    
    return render(request, 'core/contabilidad/obligacion_form.html', context)


@admin_required
def pago_obligacion_registrar(request, obligacion_id):
    """Registrar pago de una obligación fiscal. (Solo administradores)"""
    profile = get_request_profile(request)
    obligacion = get_object_or_404(ObligacionFiscal, pk=obligacion_id)
    
    # Verificación adicional: admin debe tener acceso a esta propiedad
    if not can_access_property(profile, obligacion.propiedad):
        messages.error(request, 'No tienes permiso para registrar pagos en esta propiedad.')
        return redirect('dashboard')
    
    form = PagoObligacionForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        pago = form.save(commit=False)
        pago.obligacion = obligacion
        pago.save()
        
        # Actualizar próxima fecha de vencimiento según frecuencia
        if obligacion.frecuencia_pago == 'MENSUAL':
            obligacion.fecha_vencimiento_proximo = obligacion.fecha_vencimiento_proximo + relativedelta(months=1)
        elif obligacion.frecuencia_pago == 'TRIMESTRAL':
            obligacion.fecha_vencimiento_proximo = obligacion.fecha_vencimiento_proximo + relativedelta(months=3)
        elif obligacion.frecuencia_pago == 'SEMESTRAL':
            obligacion.fecha_vencimiento_proximo = obligacion.fecha_vencimiento_proximo + relativedelta(months=6)
        elif obligacion.frecuencia_pago == 'ANUAL':
            obligacion.fecha_vencimiento_proximo = obligacion.fecha_vencimiento_proximo + relativedelta(years=1)
        
        obligacion.save()
        messages.success(request, f'Pago registrado. Próximo vencimiento: {obligacion.fecha_vencimiento_proximo}')
        return redirect('obligaciones_fiscales_lista', propiedad_id=obligacion.propiedad.id)
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        obligacion=obligacion,
        titulo=f'Registrar Pago - {obligacion.get_tipo_obligacion_display()}',
    )
    
    return render(request, 'core/contabilidad/pago_obligacion_form.html', context)


# ========== GESTIÓN DE SERVICIOS DE MANTENIMIENTO ==========

@admin_required
def contratos_mantenimiento_lista(request, propiedad_id=None):
    """Lista de contratos de mantenimiento y servicios."""
    profile = get_request_profile(request)
    
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
        contratos = ContratoMantenimiento.objects.filter(propiedad=propiedad).order_by('estado', 'fecha_proximo_pago')
    else:
        propiedades = visible_properties_for(profile)
        contratos = ContratoMantenimiento.objects.filter(propiedad__in=propiedades).order_by('-estado', 'fecha_proximo_pago')
    
    activos = contratos.filter(estado='ACTIVO')
    suspendidos = contratos.filter(estado='SUSPENDIDO')
    expirados = contratos.filter(estado='EXPIRADO')
    
    total_mensual = sum(c.costo_mensual for c in activos)
    
    context = build_context(
        request,
        'contabilidad',
        activos=activos,
        suspendidos=suspendidos,
        expirados=expirados,
        total_mensual=total_mensual,
        propiedad_id=propiedad_id,
    )
    
    return render(request, 'core/contabilidad/contratos_lista.html', context)


@admin_required
def contrato_crear(request, propiedad_id=None):
    """Crear nuevo contrato de mantenimiento."""
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    else:
        propiedad = None
    
    form = ContratoMantenimientoForm(
        request.POST or None,
        user=request.user,
        propiedad=propiedad
    )
    
    if request.method == 'POST' and form.is_valid():
        contrato = form.save(commit=False)
        if propiedad and not contrato.propiedad:
            contrato.propiedad = propiedad
        contrato.save()
        messages.success(request, f'Contrato {contrato.proveedor} creado.')
        return redirect('contratos_mantenimiento_lista', propiedad_id=propiedad_id) if propiedad_id else redirect('contratos_mantenimiento_lista')
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        propiedad=propiedad,
        titulo='Nuevo Contrato de Mantenimiento',
    )
    
    return render(request, 'core/contabilidad/contrato_form.html', context)


@admin_required
def contrato_editar(request, pk):
    """Editar contrato de mantenimiento."""
    contrato = get_object_or_404(ContratoMantenimiento, pk=pk)
    form = ContratoMantenimientoForm(
        request.POST or None,
        instance=contrato,
        user=request.user,
        propiedad=contrato.propiedad
    )
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contrato actualizado.')
        return redirect('contratos_mantenimiento_lista', propiedad_id=contrato.propiedad.id)
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        contrato=contrato,
        titulo=f'Editar Contrato - {contrato.proveedor}',
    )
    
    return render(request, 'core/contabilidad/contrato_form.html', context)


# ========== GESTIÓN DE SERVICIOS PÚBLICOS ==========

@admin_required
def servicios_publicos_lista(request, propiedad_id=None):
    """Lista de gastos de servicios públicos."""
    profile = get_request_profile(request)
    hoy = date.today()
    mes_actual = hoy.replace(day=1)
    
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
        servicios = GastoServicioPublico.objects.filter(propiedad=propiedad)
    else:
        propiedades = visible_properties_for(profile)
        servicios = GastoServicioPublico.objects.filter(propiedad__in=propiedades)
    
    # Filtrar por mes
    servicios_mes = servicios.filter(periodo_mes__month=mes_actual.month, periodo_mes__year=mes_actual.year).order_by('tipo_servicio')
    servicios_otros = servicios.exclude(periodo_mes__month=mes_actual.month).order_by('-periodo_mes')
    
    total_mes = servicios_mes.aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
    
    context = build_context(
        request,
        'contabilidad',
        servicios_mes=servicios_mes,
        servicios_otros=servicios_otros,
        total_mes=total_mes,
        propiedad_id=propiedad_id,
    )
    
    return render(request, 'core/contabilidad/servicios_publicos_lista.html', context)


@admin_required
def servicio_publico_crear(request, propiedad_id=None):
    """Registrar nuevo gasto de servicio público."""
    if propiedad_id:
        propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    else:
        propiedad = None
    
    form = GastoServicioPublicoForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        gasto = form.save(commit=False)
        if propiedad:
            gasto.propiedad = propiedad
        gasto.save()
        messages.success(request, 'Gasto de servicio registrado.')
        return redirect('servicios_publicos_lista', propiedad_id=propiedad_id) if propiedad_id else redirect('servicios_publicos_lista')
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        propiedad=propiedad,
        titulo='Registrar Gasto de Servicio Público',
    )
    
    return render(request, 'core/contabilidad/servicio_publico_form.html', context)


@admin_required
def servicio_publico_editar(request, pk):
    """Editar gasto de servicio público."""
    servicio = get_object_or_404(GastoServicioPublico, pk=pk)
    form = GastoServicioPublicoForm(request.POST or None, instance=servicio)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Gasto actualizado correctamente.')
        return redirect('servicios_publicos_lista')
    
    context = build_context(
        request,
        'contabilidad',
        form=form,
        titulo='Editar Gasto de Servicio',
    )
    
    return render(request, 'core/contabilidad/servicio_publico_form.html', context)


@admin_required
@require_POST
def servicio_publico_eliminar(request, pk):
    """Eliminar gasto de servicio público."""
    servicio = get_object_or_404(GastoServicioPublico, pk=pk)
    servicio.delete()
    messages.success(request, 'Gasto eliminado correctamente.')
    return redirect('servicios_publicos_lista')


# ========== REPORTES Y CONSOLIDADOS ===========

@admin_required
def reporte_mensual(request, propiedad_id, periodo_mes=None):
    """Reporte contable mensual consolidado."""
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    
    if periodo_mes:
        try:
            periodo = datetime.strptime(periodo_mes, '%Y-%m').date()
        except:
            periodo = date.today().replace(day=1)
    else:
        periodo = date.today().replace(day=1)
    
    # Generar o recuperar reporte
    reporte = GeneradorReportesContables.generar_reporte_mensual(propiedad, periodo)
    
    # Detalles adicionales
    nominas = NominaEmpleado.objects.filter(
        empleado__propiedad=propiedad,
        periodo_mes=periodo
    ).order_by('empleado__nombre_completo')
    
    servicios = GastoServicioPublico.objects.filter(
        propiedad=propiedad,
        periodo_mes__month=periodo.month,
        periodo_mes__year=periodo.year
    ).order_by('tipo_servicio')
    
    contratos_activos = ContratoMantenimiento.objects.filter(
        propiedad=propiedad,
        estado='ACTIVO'
    )
    
    context = build_context(
        request,
        'contabilidad',
        reporte=reporte,
        nominas=nominas,
        servicios=servicios,
        contratos_activos=contratos_activos,
        periodo=periodo,
        meses_disponibles=ReporteContableMensual.objects.filter(
            propiedad=propiedad
        ).values_list('periodo_mes', flat=True).distinct().order_by('-periodo_mes')[:12],
    )
    
    return render(request, 'core/contabilidad/reporte_mensual.html', context)


@admin_required
def reporte_anual(request, propiedad_id, año=None):
    """Reporte contable anual consolidado."""
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    
    if año is None:
        año = date.today().year
    
    reporte_anual = GeneradorReportesContables.obtener_resumen_gastos_anuales(propiedad, año)
    
    context = build_context(
        request,
        'contabilidad',
        reporte_anual=reporte_anual,
        propiedad=propiedad,
        año=año,
        años_disponibles=range(date.today().year, date.today().year - 5, -1),
    )
    
    return render(request, 'core/contabilidad/reporte_anual.html', context)


@admin_required  
def tendencias_financieras(request, propiedad_id):
    """Análisis de tendencias financieras y gastos."""
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    
    comparativa = AnalizadorTendenciasFinancieras.obtener_comparativa_gastos_ultimos_3_meses(propiedad)
    alertas = AnalizadorTendenciasFinancieras.alertas_incumplimiento_fiscal(propiedad)
    proximosGastos = GeneradorReportesContables.obtener_gastos_proximo_30_dias(propiedad)
    
    context = build_context(
        request,
        'contabilidad',
        comparativa=comparativa,
        alertas=alertas,
        proximo_mes=proximosGastos,
        propiedad=propiedad,
    )
    
    return render(request, 'core/contabilidad/tendencias.html', context)


# ========== EXPORTACIÓN A EXCEL Y PDF ==========

@admin_required
def reporte_excel(request, mes=None, anio=None):
    """Exportar reporte mensual a Excel. (Solo administradores)"""
    profile = get_request_profile(request)
    
    # Verificación adicional de seguridad
    if not (profile.es_admin and request.user.is_active):
        messages.error(request, 'No tienes autorización para exportar reportes.')
        return redirect('dashboard')
    
    propiedades = visible_properties_for(profile)
    
    if mes is None or anio is None:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    try:
        # Recuperar datos del reporte
        periodo_mes = date(anio, mes, 1)
        nominas = NominaEmpleado.objects.filter(
            empleado__propiedad__in=propiedades,
            periodo_mes=periodo_mes
        )

        servicios = GastoServicioPublico.objects.filter(
            propiedad__in=propiedades,
            periodo_mes__month=mes,
            periodo_mes__year=anio
        )

        # Generar Excel con openpyxl
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Mensual"
        
        # Estilos
        titulo_font = Font(name='Calibri', size=14, bold=True, color='FFFFFF')
        titulo_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        
        # Título
        ws.merge_cells('A1:H1')
        cell = ws['A1']
        cell.value = f'REPORTE CONTABLE - {periodo_mes.strftime("%B %Y")}'
        cell.font = titulo_font
        cell.fill = titulo_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 25
        
        # Nóminas
        row = 3
        ws.merge_cells(f'A{row}:H{row}')
        cell = ws[f'A{row}']
        cell.value = 'NÓMINAS'
        cell.font = Font(bold=True, size=12)
        
        row = 4
        for col, header in enumerate(['Empleado', 'Cédula', 'Cargo', 'Salario Base', 'Deducciones', 'Aportes', 'Neto', 'Estado'], 1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
        
        row = 5
        for nomina in nominas:
            ws.cell(row=row, column=1).value = f"{nomina.empleado.nombres} {nomina.empleado.apellidos}"
            ws.cell(row=row, column=2).value = nomina.empleado.cedula
            ws.cell(row=row, column=3).value = nomina.empleado.cargo
            ws.cell(row=row, column=4).value = float(nomina.salario_base)
            ws.cell(row=row, column=5).value = float(nomina.total_descuentos)
            ws.cell(row=row, column=6).value = float(nomina.total_aportes_patronales)
            ws.cell(row=row, column=7).value = float(nomina.total_neto)
            ws.cell(row=row, column=8).value = nomina.estado
            row += 1
        
        # Servicios públicos
        row += 2
        ws.merge_cells(f'A{row}:D{row}')
        cell = ws[f'A{row}']
        cell.value = 'SERVICIOS PÚBLICOS'
        cell.font = Font(bold=True, size=12)
        
        row += 1
        for col, header in enumerate(['Tipo', 'Período', 'Monto', 'Estado'], 1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
        
        row += 1
        for servicio in servicios:
            ws.cell(row=row, column=1).value = servicio.get_tipo_servicio_display()
            ws.cell(row=row, column=2).value = servicio.periodo_mes.strftime('%m/%Y')
            ws.cell(row=row, column=3).value = float(servicio.monto_total)
            ws.cell(row=row, column=4).value = 'Estimado' if servicio.es_estimacion else 'Real'
            row += 1

        # Obligaciones fiscales
        obligaciones = ObligacionFiscal.objects.filter(
            propiedad__in=propiedades,
            activa=True
        ).order_by('fecha_vencimiento_proximo')

        row += 2
        ws.merge_cells(f'A{row}:D{row}')
        cell = ws[f'A{row}']
        cell.value = 'OBLIGACIONES FISCALES'
        cell.font = Font(bold=True, size=12)

        row += 1
        for col, header in enumerate(['Tipo', 'Descripción', 'Monto', 'Próx. Vencimiento', 'Frecuencia', 'Referencia'], 1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill

        row += 1
        for ob in obligaciones:
            ws.cell(row=row, column=1).value = ob.get_tipo_obligacion_display()
            ws.cell(row=row, column=2).value = ob.descripcion or '-'
            ws.cell(row=row, column=3).value = float(ob.monto_obligacion)
            ws.cell(row=row, column=4).value = ob.fecha_vencimiento_proximo.strftime('%d/%m/%Y')
            ws.cell(row=row, column=5).value = ob.get_frecuencia_pago_display()
            ws.cell(row=row, column=6).value = ob.referencia_externa or '-'
            row += 1

        # Contratos de mantenimiento
        contratos = ContratoMantenimiento.objects.filter(
            propiedad__in=propiedades,
            estado='ACTIVO'
        ).order_by('fecha_proximo_pago')

        row += 2
        ws.merge_cells(f'A{row}:D{row}')
        cell = ws[f'A{row}']
        cell.value = 'CONTRATOS DE MANTENIMIENTO'
        cell.font = Font(bold=True, size=12)

        row += 1
        for col, header in enumerate(['Servicio', 'Proveedor', 'Costo Mensual', 'Próx. Pago', 'Estado'], 1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill

        row += 1
        for contrato in contratos:
            ws.cell(row=row, column=1).value = contrato.get_tipo_servicio_display()
            ws.cell(row=row, column=2).value = contrato.proveedor
            ws.cell(row=row, column=3).value = float(contrato.costo_mensual)
            ws.cell(row=row, column=4).value = contrato.fecha_proximo_pago.strftime('%d/%m/%Y')
            ws.cell(row=row, column=5).value = contrato.estado
            row += 1
        
        # Ajustar ancho de columnas
        for col in range(1, 9):
            ws.column_dimensions[chr(64 + col)].width = 15
        
        # Generar respuesta
        from io import BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_{periodo_mes.strftime("%m_%Y")}.xlsx"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generando Excel: {str(e)}')
        return redirect('contabilidad_dashboard')


@admin_required
def reporte_pdf(request, mes=None, anio=None):
    """Exportar reporte mensual a PDF. (Solo administradores)"""
    profile = get_request_profile(request)
    
    # Verificación adicional de seguridad
    if not (profile.es_admin and request.user.is_active):
        messages.error(request, 'No tienes autorización para exportar reportes.')
        return redirect('dashboard')
    
    propiedades = visible_properties_for(profile)
    
    if mes is None or anio is None:
        hoy = date.today()
        mes = hoy.month
        anio = hoy.year
    
    try:
        periodo_mes = date(anio, mes, 1)
        
        nominas = NominaEmpleado.objects.filter(
            empleado__propiedad__in=propiedades,
            periodo_mes=periodo_mes
        )

        servicios = GastoServicioPublico.objects.filter(
            propiedad__in=propiedades,
            periodo_mes__month=mes,
            periodo_mes__year=anio
        )

        obligaciones = ObligacionFiscal.objects.filter(
            propiedad__in=propiedades,
            activa=True
        ).order_by('fecha_vencimiento_proximo')

        contratos = ContratoMantenimiento.objects.filter(
            propiedad__in=propiedades,
            estado='ACTIVO'
        ).order_by('fecha_proximo_pago')

        # Crear contenido HTML
        html_content = f"""
        <h2 style="text-align: center; color: #1F4E78;">REPORTE CONTABLE MENSUAL</h2>
        <p style="text-align: center; font-size: 12pt;">{periodo_mes.strftime('%B de %Y')}</p>

        <h3>Resumen de Nóminas</h3>
        <table>
            <thead>
                <tr>
                    <th>Empleado</th>
                    <th>Cédula</th>
                    <th>Cargo</th>
                    <th>Salario Base</th>
                    <th>Deducciones</th>
                    <th>Aportes Patronales</th>
                    <th>Neto a Pagar</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
        """

        total_neto = Decimal('0')
        total_aportes = Decimal('0')
        for nomina in nominas:
            total_neto += nomina.total_neto
            total_aportes += nomina.total_aportes_patronales
            html_content += f"""
                <tr>
                    <td>{nomina.empleado.nombres} {nomina.empleado.apellidos}</td>
                    <td>{nomina.empleado.cedula}</td>
                    <td>{nomina.empleado.cargo}</td>
                    <td class="text-right">${nomina.salario_base:,.0f}</td>
                    <td class="text-right">${nomina.total_descuentos:,.0f}</td>
                    <td class="text-right">${nomina.total_aportes_patronales:,.0f}</td>
                    <td class="text-right"><strong>${nomina.total_neto:,.0f}</strong></td>
                    <td class="text-center">{nomina.estado}</td>
                </tr>
            """

        html_content += f"""
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="6">TOTAL NÓMINA NETA</td>
                    <td class="text-right"><strong>${total_neto:,.0f}</strong></td>
                    <td></td>
                </tr>
            </tfoot>
        </table>

        <h3>Servicios Públicos</h3>
        <table>
            <thead>
                <tr>
                    <th>Tipo de Servicio</th>
                    <th>Período</th>
                    <th>Proveedor</th>
                    <th>Monto</th>
                    <th>Tipo</th>
                </tr>
            </thead>
            <tbody>
        """

        total_servicios = Decimal('0')
        for servicio in servicios:
            total_servicios += servicio.monto_total
            html_content += f"""
                <tr>
                    <td>{servicio.get_tipo_servicio_display()}</td>
                    <td>{servicio.periodo_mes.strftime('%m/%Y')}</td>
                    <td>{servicio.proveedor or '-'}</td>
                    <td class="text-right">${servicio.monto_total:,.0f}</td>
                    <td>{'Estimado' if servicio.es_estimacion else 'Real'}</td>
                </tr>
            """

        html_content += f"""
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="3">TOTAL SERVICIOS</td>
                    <td class="text-right"><strong>${total_servicios:,.0f}</strong></td>
                    <td></td>
                </tr>
            </tfoot>
        </table>

        <h3>Obligaciones Fiscales Activas</h3>
        <table>
            <thead>
                <tr>
                    <th>Tipo</th>
                    <th>Descripción</th>
                    <th>Monto</th>
                    <th>Próx. Vencimiento</th>
                    <th>Frecuencia</th>
                    <th>Referencia</th>
                </tr>
            </thead>
            <tbody>
        """

        total_obligaciones = Decimal('0')
        for ob in obligaciones:
            total_obligaciones += ob.monto_obligacion
            vencida_class = ' style="color:red;"' if ob.esta_vencida else ''
            html_content += f"""
                <tr>
                    <td>{ob.get_tipo_obligacion_display()}</td>
                    <td>{ob.descripcion or '-'}</td>
                    <td class="text-right">${ob.monto_obligacion:,.0f}</td>
                    <td class="text-center"{vencida_class}>{ob.fecha_vencimiento_proximo.strftime('%d/%m/%Y')}</td>
                    <td>{ob.get_frecuencia_pago_display()}</td>
                    <td>{ob.referencia_externa or '-'}</td>
                </tr>
            """

        html_content += f"""
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="2">TOTAL OBLIGACIONES</td>
                    <td class="text-right"><strong>${total_obligaciones:,.0f}</strong></td>
                    <td colspan="3"></td>
                </tr>
            </tfoot>
        </table>

        <h3>Contratos de Mantenimiento Activos</h3>
        <table>
            <thead>
                <tr>
                    <th>Servicio</th>
                    <th>Proveedor</th>
                    <th>Costo Mensual</th>
                    <th>Próx. Pago</th>
                    <th>Teléfono</th>
                </tr>
            </thead>
            <tbody>
        """

        total_contratos = Decimal('0')
        for contrato in contratos:
            total_contratos += contrato.costo_mensual
            html_content += f"""
                <tr>
                    <td>{contrato.get_tipo_servicio_display()}</td>
                    <td>{contrato.proveedor}</td>
                    <td class="text-right">${contrato.costo_mensual:,.0f}</td>
                    <td class="text-center">{contrato.fecha_proximo_pago.strftime('%d/%m/%Y')}</td>
                    <td>{contrato.telefono_proveedor or '-'}</td>
                </tr>
            """

        gran_total = total_neto + total_aportes + total_servicios + total_obligaciones + total_contratos
        html_content += f"""
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="2">TOTAL MANTENIMIENTO</td>
                    <td class="text-right"><strong>${total_contratos:,.0f}</strong></td>
                    <td colspan="2"></td>
                </tr>
            </tfoot>
        </table>

        <div class="resumen">
            <h3>Resumen de Totales</h3>
            <div class="resumen-item"><label>Nómina Neta:</label><span class="valor">${total_neto:,.0f}</span></div>
            <div class="resumen-item"><label>Aportes Patronales:</label><span class="valor">${total_aportes:,.0f}</span></div>
            <div class="resumen-item"><label>Servicios Públicos:</label><span class="valor">${total_servicios:,.0f}</span></div>
            <div class="resumen-item"><label>Obligaciones Fiscales:</label><span class="valor">${total_obligaciones:,.0f}</span></div>
            <div class="resumen-item"><label>Contratos Mantenimiento:</label><span class="valor">${total_contratos:,.0f}</span></div>
            <div class="resumen-item" style="border-top:2px solid #1F4E78; margin-top:8px; padding-top:8px; font-size:13pt;">
                <label>GRAN TOTAL:</label><span class="valor"><strong>${gran_total:,.0f}</strong></span>
            </div>
        </div>
        """

        # Generar PDF
        html_completo = ExportadorPDF.generar_reporte_html(
            f'Reporte Contable - {periodo_mes.strftime("%B %Y")}',
            html_content
        )
        pdf_bytes = ExportadorPDF.generar_pdf(html_completo)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_{periodo_mes.strftime("%m_%Y")}.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generando PDF: {str(e)}')
        return redirect('contabilidad_dashboard')


@admin_required
def nomina_excel(request):
    """Exportar nóminas del mes actual a Excel. (Solo administradores)"""
    profile = get_request_profile(request)
    
    # Verificación adicional de seguridad
    if not (profile.es_admin and request.user.is_active):
        messages.error(request, 'No tienes autorización para exportar nóminas.')
        return redirect('dashboard')
    
    propiedades = visible_properties_for(profile)
    
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    
    nominas = NominaEmpleado.objects.filter(
        empleado__propiedad__in=propiedades,
        periodo_mes=inicio_mes
    ).order_by('empleado__nombres')
    
    archivo = exportar_nominas_excel(nominas, propiedades[0] if propiedades else None)
    
    response = HttpResponse(
        archivo.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="nominas_{inicio_mes.strftime("%m_%Y")}.xlsx"'
    return response


@admin_required
def obligaciones_excel(request):
    """Exportar obligaciones fiscales a Excel. (Solo administradores)"""
    profile = get_request_profile(request)
    
    # Verificación adicional de seguridad
    if not (profile.es_admin and request.user.is_active):
        messages.error(request, 'No tienes autorización para exportar obligaciones.')
        return redirect('dashboard')
    
    propiedades = visible_properties_for(profile)
    
    obligaciones = ObligacionFiscal.objects.filter(
        propiedad__in=propiedades,
        activa=True
    ).order_by('fecha_vencimiento_proximo')
    
    archivo = exportar_obligaciones_excel(obligaciones, propiedades[0] if propiedades else None)
    
    response = HttpResponse(
        archivo.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="obligaciones_fiscales.xlsx"'
    return response
