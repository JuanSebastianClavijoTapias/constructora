"""
Módulo de cálculos contables y financieros para gestión de propiedades en Colombia.
Implementa regulaciones laborales, impositivas y deducciones obligatorias colombianas 2024.

REFERENCIAS NORMATIVAS 2024:
- SMMLV 2024: $1.600.000 COP
- Auxilio de Transporte: $162.000 COP
- AUX_TRANSPORTE_LIMITE: SMMLV * 2 = $3.200.000
- Aportes a pensión: 4% empleado + 12% empleador
- Aportes a salud: 4% empleado + 8.5% empleador (afiliaciones solidarias)
- SENA: 2% (empleador sobre nómina)
- ICBF: 3% (empleador sobre nómina)
- Caja de Compensación: 4% (empleador sobre nómina)
- ARL: Variable según actividad (0.348% - 8.7%), promedio 5.22%
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import Dict, Tuple, List
from django.db.models import Sum, Q
from .models import (
    PersonalEmpleado, NominaEmpleado, GastoServicioPublico,
    ContratoMantenimiento, ObligacionFiscal, ReporteContableMensual,
    PagoMantenimiento, EquiposUniformes
)


# ========== CONSTANTES COLOMBIA 2024 ==========

class ConstantesColombiana2024:
    """Constantes normativas laborales y fiscales Colombia 2024."""
    
    # Salario mínimo
    SMMLV = Decimal('1600000')
    AUXILIO_TRANSPORTE = Decimal('162000')
    AUXILIO_TRANSPORTE_LIMITE = SMMLV * 2  # $3.200.000
    
    # Aportes obligatorios del empleado (descuentos)
    APORTE_PENSION_EMPLEADO = Decimal('0.04')  # 4%
    APORTE_SALUD_EMPLEADO = Decimal('0.04')    # 4%
    FONDO_SOLIDARIDAD = Decimal('0.01')        # 1% si salario > 4*SMMLV
    LIMITE_FONDO_SOLIDARIDAD = SMMLV * 4      # $6.400.000
    
    # Aportes obligatorios del empleador
    APORTE_PENSION_EMPLEADOR = Decimal('0.12')  # 12%
    APORTE_SALUD_EMPLEADOR = Decimal('0.085')   # 8.5% (promedio)
    SENA = Decimal('0.02')                      # 2%
    ICBF = Decimal('0.03')                      # 3%
    CAJA_COMPENSACION = Decimal('0.04')        # 4%
    ARL_PROMEDIO = Decimal('0.0522')           # 5.22% (promedio, varía por sector)
    
    # Tasas de interés por incumplimiento (referencias)
    INTERES_MORATORIO_ANUAL = Decimal('0.15')  # 15% anual
    TASA_GMF = Decimal('0.004')                # 0.4% sobre movimientos


class CalculadoraNomina:
    """Calculadora de nómina según regulaciones colombianas."""
    
    def __init__(self):
        self.constantes = ConstantesColombiana2024()
    
    def calcular_nomina_completa(self, nomina: NominaEmpleado) -> NominaEmpleado:
        """
        Calcula automáticamente todas las deducciones y aportes de una nómina
        según la ley colombiana vigente.
        
        Args:
            nomina: Instancia de NominaEmpleado
            
        Returns:
            NominaEmpleado con todos los campos calculados
        """
        return nomina.calcular_deducciones_y_aportes()
    
    def calcular_aporte_arl(self, salario_base: Decimal, tipo_empleado: str) -> Decimal:
        """
        Calcula el aporte de ARL (Seguro de Riesgo Laboral) según categoría.
        
        Categorías de riesgo (tasas 2024 - aproximadas):
        - COMERCIO/SERVICIOS: 0.348% - 0.696%
        - INDUSTRIA LIVIANA: 1.044% - 2.088%
        - CONSTRUCCION: 4.176% - 7.2%
        - MINERIA: Hasta 8.7%
        
        Para empleados de edificios (mantenimiento, portería): 1-2%
        """
        categorias_riesgo = {
            'PORTERO': Decimal('0.01'),           # 1% - bajo riesgo
            'CONSERJE': Decimal('0.0104'),        # 1.04% - bajo riesgo
            'LIMPIEZA': Decimal('0.0152'),        # 1.52% - riesgo moderado
            'JARDINERO': Decimal('0.0254'),       # 2.54% - riesgo moderado-alto
            'SEGURIDAD': Decimal('0.0676'),       # 6.76% - riesgo alto
            'OTRO': Decimal('0.0522'),            # 5.22% - promedio
        }
        
        tasa = categorias_riesgo.get(tipo_empleado, self.constantes.ARL_PROMEDIO)
        return (salario_base * tasa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_provision_cesantia(self, salario: Decimal, meses: int = 1) -> Decimal:
        """
        Calcula la provisión de cesantía (1 mes de salario por año).
        Típicamente se provee mensualmente: salario / 12
        """
        cesantia_mensual = (salario * Decimal('30')) / Decimal('360')
        return (cesantia_mensual * Decimal(meses)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_prima_servicios(self, salario: Decimal, meses: int = 6) -> Decimal:
        """
        Calcula prima de servicios (1 mes cada 6 meses).
        Se provee mensualmente: (salario * 6) / 180 días
        """
        prima_diaria = (salario * Decimal(meses)) / Decimal('180')
        return (prima_diaria).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_retencion_fuente(self, salario: Decimal) -> Decimal:
        """
        Calcula retención en la fuente aproximada para empleados.
        Tabla de retención 2024 (simplificada por UVT: $43.348)
        
        Rangos base de retención:
        - Hasta 95 UVT (~$4.118.060): 0%
        - 95 - 150 UVT (~$4.118.060 - $6.502.200): 5%
        - 150 - 360 UVT (>$6.502.200): 19%
        
        Para empleados de servicios (típicamente salarios bajos): generalmente no aplica
        """
        UVT_2024 = Decimal('43348')
        LIMITE_1 = UVT_2024 * Decimal('95')  # ~$4.118.060
        LIMITE_2 = UVT_2024 * Decimal('150')  # ~$6.502.200
        
        if salario <= LIMITE_1:
            return Decimal('0')
        elif salario <= LIMITE_2:
            excedente = salario - LIMITE_1
            return (excedente * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            # Tramo 1: hasta máximo de tramo 1
            tramo_1 = (LIMITE_2 - LIMITE_1) * Decimal('0.05')
            # Tramo 2: resto
            excedente = salario - LIMITE_2
            tramo_2 = excedente * Decimal('0.19')
            return (tramo_1 + tramo_2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class GeneradorReportesContables:
    """Genera reportes contables consolidados mensuales."""
    
    @staticmethod
    def generar_reporte_mensual(propiedad, periodo_mes: date) -> ReporteContableMensual:
        """
        Genera reporte contable mensual consolidado para una propiedad.
        
        Consolidar:
        1. Nómina: salarios, deducciones, aportes patronales, equipos
        2. Obligaciones fiscales pagadas en el mes
        3. Mantenimiento: contratos activos
        4. Servicios públicos: gastos registrados
        
        Args:
            propiedad: Instancia de Propiedad
            periodo_mes: Primer día del mes (datetime.date)
        """
        from dateutil.relativedelta import relativedelta
        
        inicio_mes = periodo_mes.replace(day=1)
        fin_mes = (inicio_mes + relativedelta(months=1)) - timedelta(days=1)
        
        # Obtener o crear reporte
        reporte, creado = ReporteContableMensual.objects.get_or_create(
            propiedad=propiedad,
            periodo_mes=inicio_mes,
        )
        
        # === NÓMINA ===
        nominas = NominaEmpleado.objects.filter(
            empleado__propiedad=propiedad,
            periodo_mes=inicio_mes
        ).select_related('empleado')
        
        total_salarios = nominas.aggregate(Sum('salario_base'))['salario_base__sum'] or Decimal('0')
        total_deducciones = nominas.aggregate(Sum('total_descuentos'))['total_descuentos__sum'] or Decimal('0')
        total_neto = nominas.aggregate(Sum('total_neto'))['total_neto__sum'] or Decimal('0')
        total_aportes_patronales = nominas.aggregate(Sum('total_aportes_patronales'))['total_aportes_patronales__sum'] or Decimal('0')
        
        # Equipos y uniformes
        equipos = EquiposUniformes.objects.filter(
            empleado__propiedad=propiedad,
            fecha_asignacion__month=inicio_mes.month,
            fecha_asignacion__year=inicio_mes.year
        ).aggregate(total=Sum('costo_unitario'))
        total_equipos = equipos['total'] or Decimal('0')
        
        reporte.total_salarios_base = total_salarios
        reporte.total_deducciones_empleados = total_deducciones
        reporte.total_neto_nómina = total_neto
        reporte.total_aportes_patronales = total_aportes_patronales
        reporte.total_equipos_uniformes = total_equipos
        reporte.subtotal_personal = total_salarios + total_aportes_patronales + total_equipos
        
        # === OBLIGACIONES FISCALES PAGADAS ===
        # Este mes se consolidarán los pagos realizados
        # (En una versión más completa, se consultarían PagoObligacion)
        reporte.total_obligaciones_fiscales = Decimal('0')
        
        # === MANTENIMIENTO ===
        mantenimientos_activos = ContratoMantenimiento.objects.filter(
            propiedad=propiedad,
            estado='ACTIVO',
            fecha_inicio__lte=fin_mes,
        ).exclude(
            fecha_fin__lt=inicio_mes,
            fecha_fin__isnull=False
        )
        
        total_mantenimiento = Decimal('0')
        for contrato in mantenimientos_activos:
            # En un mes puede haber 4-5 semanas de servicio según fechas
            total_mantenimiento += contrato.costo_mensual
        
        reporte.total_mantenimiento = total_mantenimiento
        
        # === SERVICIOS PÚBLICOS ===
        servicios = GastoServicioPublico.objects.filter(
            propiedad=propiedad,
            periodo_mes__month=inicio_mes.month,
            periodo_mes__year=inicio_mes.year
        )
        
        total_servicios = servicios.aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
        reporte.total_servicios_publicos = total_servicios
        
        # Desglose de servicios
        reporte.detalle_electricidad = servicios.filter(
            tipo_servicio__in=['ELECTRICIDAD_AREAS_COMUNES', 'ELECTRICIDAD_BOMBAS', 'ELECTRICIDAD_ASCENSORES']
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
        
        reporte.detalle_agua = servicios.filter(
            tipo_servicio__in=['AGUA_RIEGO', 'AGUA_LIMPIEZA']
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
        
        reporte.detalle_gas = servicios.filter(
            tipo_servicio='GAS_AREAS_COMUNES'
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
        
        reporte.detalle_internet = servicios.filter(
            tipo_servicio='INTERNET_TELEFONÍA'
        ).aggregate(Sum('monto_total'))['monto_total__sum'] or Decimal('0')
        
        # === CONSOLIDADO ===
        reporte.total_gastos_operacionales = (
            reporte.subtotal_personal +
            reporte.total_obligaciones_fiscales +
            reporte.total_mantenimiento +
            reporte.total_servicios_publicos
        )
        
        reporte.save()
        return reporte
    
    @staticmethod
    def obtener_gastos_proximo_30_dias(propiedad) -> Dict:
        """
        Obtiene consolidado de obligaciones/gastos próximos a vencer (30 días).
        Útil para análisis de flujo de caja.
        """
        hoy = date.today()
        proximo_mes = hoy + timedelta(days=30)
        
        obligaciones_proximas = ObligacionFiscal.objects.filter(
            propiedad=propiedad,
            activa=True,
            fecha_vencimiento_proximo__gte=hoy,
            fecha_vencimiento_proximo__lte=proximo_mes
        ).aggregate(Sum('monto_obligacion'))
        
        mantenimiento_activo = ContratoMantenimiento.objects.filter(
            propiedad=propiedad,
            estado='ACTIVO',
            fecha_proximo_pago__gte=hoy,
            fecha_proximo_pago__lte=proximo_mes
        )
        
        total_mantenimiento = sum(
            contrato.costo_mensual for contrato in mantenimiento_activo
        )
        
        return {
            'obligaciones_fiscales': obligaciones_proximas['monto_obligacion__sum'] or Decimal('0'),
            'mantenimiento': total_mantenimiento,
            'total': (obligaciones_proximas['monto_obligacion__sum'] or Decimal('0')) + total_mantenimiento,
        }
    
    @staticmethod
    def obtener_resumen_gastos_anuales(propiedad, año: int) -> Dict:
        """
        Obtiene resumen de gastos operacionales anuales por categoría.
        """
        from datetime import datetime
        
        inicio_año = date(año, 1, 1)
        fin_año = date(año, 12, 31)
        
        # Gastos por mes en un resumen anual
        reportes = ReporteContableMensual.objects.filter(
            propiedad=propiedad,
            periodo_mes__year=año
        )
        
        total_nómina = reportes.aggregate(Sum('subtotal_personal'))['subtotal_personal__sum'] or Decimal('0')
        total_obligaciones = reportes.aggregate(Sum('total_obligaciones_fiscales'))['total_obligaciones_fiscales__sum'] or Decimal('0')
        total_mantenimiento = reportes.aggregate(Sum('total_mantenimiento'))['total_mantenimiento__sum'] or Decimal('0')
        total_servicios = reportes.aggregate(Sum('total_servicios_publicos'))['total_servicios_publicos__sum'] or Decimal('0')
        
        return {
            'año': año,
            'nómina': total_nómina,
            'obligaciones_fiscales': total_obligaciones,
            'mantenimiento': total_mantenimiento,
            'servicios_públicos': total_servicios,
            'total': total_nómina + total_obligaciones + total_mantenimiento + total_servicios,
            'mes_mayor_gasto': reportes.order_by('-total_gastos_operacionales').first().periodo_mes if reportes else None,
        }


class AnalizadorTendenciasFinancieras:
    """Analiza tendencias y proporciona insights sobre gastos."""
    
    @staticmethod
    def obtener_comparativa_gastos_ultimos_3_meses(propiedad):
        """Compara gastos de los últimas 3 meses."""
        from datetime import datetime, timedelta
        
        hoy = date.today()
        hace_3_meses = hoy - timedelta(days=90)
        
        reportes = ReporteContableMensual.objects.filter(
            propiedad=propiedad,
            periodo_mes__gte=hace_3_meses.replace(day=1)
        ).order_by('periodo_mes')
        
        return {
            'meses': [r.periodo_mes.strftime('%B %Y') for r in reportes],
            'gastos': [float(r.total_gastos_operacionales) for r in reportes],
            'tendencia': 'INCREMENTO' if len(reportes) > 1 and reportes[-1].total_gastos_operacionales > reportes[0].total_gastos_operacionales else 'DECREMENTO'
        }
    
    @staticmethod
    def alertas_incumplimiento_fiscal(propiedad) -> List[str]:
        """Retorna alertas de obligaciones fiscales vencidas."""
        hoy = date.today()
        alertas = []
        
        vencidas = ObligacionFiscal.objects.filter(
            propiedad=propiedad,
            activa=True,
            fecha_vencimiento_proximo__lt=hoy
        )
        
        if vencidas.exists():
            alertas.append(f"⚠️ {vencidas.count()} obligaciones fiscales VENCIDAS")
        
        proximas = ObligacionFiscal.objects.filter(
            propiedad=propiedad,
            activa=True,
            fecha_vencimiento_proximo__gte=hoy,
            fecha_vencimiento_proximo__lte=hoy + timedelta(days=15)
        )
        
        if proximas.exists():
            alertas.append(f"⚠️ {proximas.count()} obligaciones vencen en los próximos 15 días")
        
        return alertas
