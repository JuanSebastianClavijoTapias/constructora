"""
Tests para el módulo de contabilidad.
Valida modelos, cálculos de nómina, reportes y vistas.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User

from .models import (
    Propiedad,
    PersonalEmpleado,
    NominaEmpleado,
    ObligacionFiscal,
    ContratoMantenimiento,
    GastoServicioPublico,
    ReporteContableMensual,
)
from .accounting import CalculadoraNomina, GeneradorReportesContables, ConstantesColombiana2024


class ConstantesTest(TestCase):
    """Test de las constantes normativas colombianas."""
    
    def test_smmlv_2024(self):
        """Validar SMMLV 2024."""
        constantes = ConstantesColombiana2024()
        self.assertEqual(constantes.SMMLV, Decimal('1600000'))
    
    def test_auxilio_transporte_2024(self):
        """Validar auxilio de transporte 2024."""
        constantes = ConstantesColombiana2024()
        self.assertEqual(constantes.AUXILIO_TRANSPORTE, Decimal('162000'))
    
    def test_aportes_obligatorios(self):
        """Validar porcentajes de aportes."""
        constantes = ConstantesColombiana2024()
        # Aporte pensión empleado: 4%
        self.assertEqual(constantes.APORTE_PENSION_EMPLEADO, Decimal('0.04'))
        # Aporte salud empleado: 4%
        self.assertEqual(constantes.APORTE_SALUD_EMPLEADO, Decimal('0.04'))
        # Aporte pensión empleador: 12%
        self.assertEqual(constantes.APORTE_PENSION_EMPLEADOR, Decimal('0.12'))


class PersonalEmpleadoTest(TestCase):
    """Tests para el modelo PersonalEmpleado."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Torre Central',
            direccion='Calle 5 # 10-20',
            precio_mensual=Decimal('5000000')
        )
    
    def test_crear_empleado(self):
        """Crear empleado correctamente."""
        empleado = PersonalEmpleado.objects.create(
            propiedad=self.propiedad,
            nombre_completo='Juan Pérez García',
            cedula='1234567890',
            tipo_empleado='PORTERO',
            tipo_contrato='INDEFINIDO',
            salario_mensual_base=Decimal('1600000'),
            fecha_inicio_contrato=date(2024, 1, 1),
        )
        
        self.assertEqual(empleado.nombre_completo, 'Juan Pérez García')
        self.assertEqual(empleado.tipo_empleado, 'PORTERO')
        self.assertTrue(empleado.activo)
    
    def test_empleado_activo_por_defecto(self):
        """Empleado debe estar activo por defecto."""
        empleado = PersonalEmpleado.objects.create(
            propiedad=self.propiedad,
            nombre_completo='Maria López',
            cedula='0987654321',
            tipo_empleado='LIMPIEZA',
            tipo_contrato='FIJO',
            salario_mensual_base=Decimal('1400000'),
            fecha_inicio_contrato=date(2024, 1, 1),
        )
        
        self.assertTrue(empleado.activo)


class NominaEmpleadoTest(TestCase):
    """Tests para cálculos de nómina."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Edificio Gamora',
            direccion='Carrera 7 # 50-12',
            precio_mensual=Decimal('3000000')
        )
        
        self.empleado = PersonalEmpleado.objects.create(
            propiedad=self.propiedad,
            nombre_completo='Carlos López Sánchez',
            cedula='79123456',
            tipo_empleado='PORTERO',
            tipo_contrato='INDEFINIDO',
            salario_mensual_base=Decimal('1600000'),
            fecha_inicio_contrato=date(2024, 1, 1),
        )
    
    def test_crear_nomina(self):
        """Crear nómina correctamente."""
        nomina = NominaEmpleado.objects.create(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
            aux_transporte=Decimal('162000'),
        )
        
        self.assertEqual(nomina.salario_base, Decimal('1600000'))
        self.assertEqual(nomina.estado, 'BORRADOR')
    
    def test_calcular_deducciones_pension(self):
        """Validar cálculo de aporte a pensión (4%)."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
            aux_transporte=Decimal('162000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # Aporte pensión: 4% de $1.600.000 = $64.000
        esperado = Decimal('64000')
        self.assertEqual(nomina.descuento_pension, esperado)
    
    def test_calcular_deducciones_salud(self):
        """Validar cálculo de aporte a salud (4%)."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # Aporte salud: 4% de $1.600.000 = $64.000
        esperado = Decimal('64000')
        self.assertEqual(nomina.descuento_salud, esperado)
    
    def test_fondo_solidaridad_no_aplica_bajo_salario(self):
        """Fondo de solidaridad no aplica si salario < 4 SMMLV."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('2000000'),  # Menos de 4 * SMMLV
        )
        nomina.calcular_deducciones_y_aportes()
        
        self.assertEqual(nomina.descuento_fondo_solidaridad, Decimal('0'))
    
    def test_fondo_solidaridad_aplica_alto_salario(self):
        """Fondo de solidaridad (1%) se calcula sobre excedente > 4 SMMLV."""
        salario_alto = Decimal('8000000')  # > 4 * SMMLV (6.4M)
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=salario_alto,
        )
        nomina.calcular_deducciones_y_aportes()
        
        # Excedente: 8.000.000 - 6.400.000 = 1.600.000
        # Fondo: 1% de 1.600.000 = 16.000
        esperado = Decimal('16000')
        self.assertEqual(nomina.descuento_fondo_solidaridad, esperado)
    
    def test_calcular_aporte_patronal_pension(self):
        """Validar aporte patronal a pensión (12%)."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # Aporte patrón pensión: 12% de $1.600.000 = $192.000
        esperado = Decimal('192000')
        self.assertEqual(nomina.aporte_pension_patronal, esperado)
    
    def test_total_neto_correcto(self):
        """Validar que total neto = devengado - descuentos."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
            aux_transporte=Decimal('162000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # Devengado: 1.600.000 + 162.000 = 1.762.000
        # Descuentos: 64.000 (pensión) + 64.000 (salud) = 128.000
        # Neto: 1.762.000 - 128.000 = 1.634.000
        esperado_neto = Decimal('1634000')
        self.assertEqual(nomina.total_neto, esperado_neto)
    
    def test_aporte_sena(self):
        """Validar aporte SENA (2%)."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # SENA: 2% de 1.600.000 = 32.000
        esperado = Decimal('32000')
        self.assertEqual(nomina.aporte_sena, esperado)
    
    def test_aporte_icbf(self):
        """Validar aporte ICBF (3%)."""
        nomina = NominaEmpleado(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
        )
        nomina.calcular_deducciones_y_aportes()
        
        # ICBF: 3% de 1.600.000 = 48.000
        esperado = Decimal('48000')
        self.assertEqual(nomina.aporte_icbf, esperado)


class CalculadoraNominaTest(TestCase):
    """Tests para la calculadora de nómina."""
    
    def setUp(self):
        self.calculador = CalculadoraNomina()
        self.propiedad = Propiedad.objects.create(
            nombre='Edificio Test',
            direccion='Test 123',
            precio_mensual=Decimal('5000000')
        )
        self.empleado = PersonalEmpleado.objects.create(
            propiedad=self.propiedad,
            nombre_completo='Test Empleado',
            cedula='12345678',
            tipo_empleado='PORTERO',
            tipo_contrato='INDEFINIDO',
            salario_mensual_base=Decimal('1600000'),
            fecha_inicio_contrato=date(2024, 1, 1),
        )
    
    def test_calcular_arl_portero(self):
        """Calcular ARL para portero (1%)."""
        arl = self.calculador.calcular_aporte_arl(Decimal('1600000'), 'PORTERO')
        # 1% de 1.600.000 = 16.000
        self.assertEqual(arl, Decimal('16000'))
    
    def test_calcular_arl_limpieza(self):
        """Calcular ARL para personal de limpieza (1.52%)."""
        arl = self.calculador.calcular_aporte_arl(Decimal('1600000'), 'LIMPIEZA')
        # 1.52% de 1.600.000 = 24.320
        self.assertEqual(arl, Decimal('24320'))
    
    def test_calcular_arl_seguridad(self):
        """Calcular ARL para seguridad (6.76%)."""
        arl = self.calculador.calcular_aporte_arl(Decimal('1600000'), 'SEGURIDAD')
        # 6.76% de 1.600.000 = 108.160
        self.assertAlmostEqual(float(arl), 108160, delta=1)
    
    def test_calcular_provision_cesantia(self):
        """Calcular provisión de cesantía monthly (salario/12)."""
        cesantia = self.calculador.calcular_provision_cesantia(Decimal('1600000'), meses=1)
        # Aproximado salario / 12 para el mes
        self.assertGreater(cesantia, Decimal('0'))


class GeneradorReportesTest(TestCase):
    """Tests para generador de reportes."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Edificio Report Test',
            direccion='Report 123',
            precio_mensual=Decimal('3000000')
        )
        
        self.empleado = PersonalEmpleado.objects.create(
            propiedad=self.propiedad,
            nombre_completo='Empleado Reporte',
            cedula='99999999',
            tipo_empleado='PORTERO',
            tipo_contrato='INDEFINIDO',
            salario_mensual_base=Decimal('1600000'),
            fecha_inicio_contrato=date(2024, 1, 1),
        )
        
        # Crear nómina
        self.nomina = NominaEmpleado.objects.create(
            empleado=self.empleado,
            periodo_mes=date(2024, 5, 1),
            salario_base=Decimal('1600000'),
        )
        self.nomina.calcular_deducciones_y_aportes()
        self.nomina.save()
    
    def test_generar_reporte_mensual(self):
        """Generar reporte contable mensual."""
        reporte = GeneradorReportesContables.generar_reporte_mensual(
            self.propiedad, 
            date(2024, 5, 1)
        )
        
        self.assertEqual(reporte.propiedad, self.propiedad)
        self.assertEqual(reporte.periodo_mes, date(2024, 5, 1))
        self.assertGreater(reporte.total_gastos_operacionales, Decimal('0'))
    
    def test_reporte_incluye_nomina(self):
        """Reporte debe incluir gastos de nómina."""
        reporte = GeneradorReportesContables.generar_reporte_mensual(
            self.propiedad,
            date(2024, 5, 1)
        )
        
        self.assertGreater(reporte.subtotal_personal, Decimal('0'))
        self.assertGreater(reporte.total_aportes_patronales, Decimal('0'))


class ObligacionFiscalTest(TestCase):
    """Tests para obligaciones fiscales."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Propiedad Fiscal',
            direccion='Fiscal 456',
            precio_mensual=Decimal('2000000')
        )
    
    def test_crear_obligacion(self):
        """Crear obligación fiscal."""
        obligacion = ObligacionFiscal.objects.create(
            propiedad=self.propiedad,
            tipo_obligacion='IMPUESTO_PREDIAL',
            monto_obligacion=Decimal('500000'),
            frecuencia_pago='ANUAL',
            fecha_vencimiento_proximo=date(2024, 12, 31),
        )
        
        self.assertEqual(obligacion.tipo_obligacion, 'IMPUESTO_PREDIAL')
        self.assertTrue(obligacion.activa)
    
    def test_obligacion_vencida(self):
        """Detectar obligación vencida."""
        obligacion = ObligacionFiscal.objects.create(
            propiedad=self.propiedad,
            tipo_obligacion='ACUEDUCTO',
            monto_obligacion=Decimal('150000'),
            frecuencia_pago='MENSUAL',
            fecha_vencimiento_proximo=date(2024, 1, 1),  # Fecha pasada
        )
        
        self.assertTrue(obligacion.esta_vencida)


class ContratoMantenimientoTest(TestCase):
    """Tests para contratos de mantenimiento."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Propiedad Mantenimiento',
            direccion='Mant 789',
            precio_mensual=Decimal('2500000')
        )
    
    def test_crear_contrato(self):
        """Crear contrato de mantenimiento."""
        contrato = ContratoMantenimiento.objects.create(
            propiedad=self.propiedad,
            tipo_servicio='ASCENSORES',
            proveedor='Elevadores Ltda',
            costo_mensual=Decimal('250000'),
            fecha_inicio=date(2024, 1, 1),
            fecha_proximo_pago=date(2024, 5, 15),
            estado='ACTIVO',
        )
        
        self.assertEqual(contrato.proveedor, 'Elevadores Ltda')
        self.assertEqual(contrato.costo_mensual, Decimal('250000'))
    
    def test_contrato_no_vencido(self):
        """Contrato sin fecha fin no debe reportarse vencido."""
        contrato = ContratoMantenimiento.objects.create(
            propiedad=self.propiedad,
            tipo_servicio='SEGURIDAD_ELECTRONICA',
            proveedor='Seguridad Inteligente',
            costo_mensual=Decimal('300000'),
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=None,
            fecha_proximo_pago=date(2024, 6, 1),
            estado='ACTIVO',
        )
        
        self.assertFalse(contrato.esta_vencido)


class GastoServicioPublicoTest(TestCase):
    """Tests para servicios públicos."""
    
    def setUp(self):
        self.propiedad = Propiedad.objects.create(
            nombre='Propiedad Servicios',
            direccion='Serv 321',
            precio_mensual=Decimal('4000000')
        )
    
    def test_crear_gasto_servicio(self):
        """Crear gasto de servicio público."""
        gasto = GastoServicioPublico.objects.create(
            propiedad=self.propiedad,
            tipo_servicio='ELECTRICIDAD_AREAS_COMUNES',
            periodo_mes=date(2024, 5, 1),
            monto_total=Decimal('450000'),
        )
        
        self.assertEqual(gasto.tipo_servicio, 'ELECTRICIDAD_AREAS_COMUNES')
        self.assertFalse(gasto.es_estimacion)
    
    def test_marcar_como_estimacion(self):
        """Marcar gasto como estimación."""
        gasto = GastoServicioPublico.objects.create(
            propiedad=self.propiedad,
            tipo_servicio='AGUA_RIEGO',
            periodo_mes=date(2024, 5, 1),
            monto_total=Decimal('200000'),
            es_estimacion=True,
        )
        
        self.assertTrue(gasto.es_estimacion)


class IntegracionViewsTest(TestCase):
    """Tests de integración de vistas."""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario admin
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='admin123',
            is_staff=True,
            is_superuser=True,
        )
        
        # Crear propiedad
        self.propiedad = Propiedad.objects.create(
            nombre='Propiedad Test Views',
            direccion='Views Test 111',
            precio_mensual=Decimal('2000000')
        )
    
    def test_dashboard_contabilidad_acceso(self):
        """Acceso a dashboard de contabilidad requiere login."""
        response = self.client.get('/contabilidad/')
        # Sin login debe redirigir a login
        self.assertEqual(response.status_code, 302)
    
    def test_empleados_lista_acceso(self):
        """Acceso a lista de empleados requiere login."""
        response = self.client.get('/contabilidad/empleados/')
        self.assertEqual(response.status_code, 302)  # Redirect a login
