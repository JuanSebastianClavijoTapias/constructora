from django.contrib.auth.models import User
from django.db import models

class Propiedad(models.Model):
    ESTADOS = (
        ('DISPONIBLE', 'Disponible'),
        ('ALQUILADA', 'Alquilada'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
    )
    
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='DISPONIBLE')
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    inquilino_nombre = models.CharField(max_length=150, blank=True, null=True)
    habitaciones = models.PositiveIntegerField(default=0, help_text='Número de habitaciones')
    baños = models.PositiveIntegerField(default=0, help_text='Número de baños')
    patio = models.BooleanField(default=False, help_text='¿Tiene patio?')
    parquedero = models.BooleanField(default=False, help_text='¿Tiene parquedero?')
    
    def __str__(self):
        return f"{self.nombre} - {self.direccion}"

    @property
    def imagen_principal(self):
        imagen = self.imagenes.first()
        if imagen:
            return imagen.imagen.url
        return self.imagen_url

    @property
    def inquilinos_resumen(self):
        perfiles = [
            perfil.nombre_mostrar
            for perfil in self.usuarios.select_related('user').all()
            if perfil.rol == PerfilUsuario.ROL_INQUILINO
        ]
        if perfiles:
            return ', '.join(perfiles)
        return self.inquilino_nombre or 'Sin inquilino asignado'

    @property
    def usuarios_casa_total(self):
        return self.usuarios.count()


class PropiedadImagen(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='propiedades/')
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creada_en', 'id']

    def __str__(self):
        return f"Imagen de {self.propiedad.nombre}"

class Pago(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('ATRASADO', 'Atrasado'),
    )
    
    METODOS_PAGO = (
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta de Crédito'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    )
    
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='pagos')
    inquilino_nombre = models.CharField(max_length=150)
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_limite = models.DateField()
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='TRANSFERENCIA')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    def __str__(self):
        return f"Pago de {self.inquilino_nombre} - {self.propiedad.nombre}"


class PerfilUsuario(models.Model):
    ROL_ADMIN = 'ADMIN'
    ROL_INQUILINO = 'INQUILINO'
    ROLES = (
        (ROL_ADMIN, 'Administrador'),
        (ROL_INQUILINO, 'Usuario de la casa'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    propiedad = models.ForeignKey(
        Propiedad,
        on_delete=models.SET_NULL,
        related_name='usuarios',
        blank=True,
        null=True,
    )
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_INQUILINO)
    telefono = models.CharField(max_length=30, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'

    def __str__(self):
        return f"{self.nombre_mostrar} ({self.get_rol_display()})"

    @property
    def nombre_mostrar(self):
        return self.user.get_full_name() or self.user.username

    @property
    def es_admin(self):
        return self.rol == self.ROL_ADMIN or self.user.is_superuser


class SolicitudSoporte(models.Model):
    CATEGORIA_FUGA = 'FUGA_AGUA'
    CATEGORIA_ELECTRICO = 'ELECTRICO'
    CATEGORIA_HUMEDAD = 'HUMEDAD'
    CATEGORIA_CERRADURA = 'CERRADURA'
    CATEGORIA_GAS = 'GAS'
    CATEGORIA_ELECTRODOMESTICO = 'ELECTRODOMESTICO'
    CATEGORIA_OTRO = 'OTRO'

    CATEGORIAS = (
        (CATEGORIA_FUGA, 'Fuga de agua'),
        (CATEGORIA_ELECTRICO, 'Problema electrico'),
        (CATEGORIA_HUMEDAD, 'Humedad o filtracion'),
        (CATEGORIA_CERRADURA, 'Puerta o cerradura'),
        (CATEGORIA_GAS, 'Gas u olor extrano'),
        (CATEGORIA_ELECTRODOMESTICO, 'Electrodomestico'),
        (CATEGORIA_OTRO, 'Otro dano'),
    )

    ESTADO_NUEVA = 'NUEVA'
    ESTADO_EN_PROCESO = 'EN_PROCESO'
    ESTADO_RESUELTA = 'RESUELTA'
    ESTADOS = (
        (ESTADO_NUEVA, 'Nueva'),
        (ESTADO_EN_PROCESO, 'En proceso'),
        (ESTADO_RESUELTA, 'Resuelta'),
    )

    PRIORIDAD_ALTA = 'ALTA'
    PRIORIDAD_MEDIA = 'MEDIA'
    PRIORIDAD_BAJA = 'BAJA'
    PRIORIDADES = (
        (PRIORIDAD_ALTA, 'Alta'),
        (PRIORIDAD_MEDIA, 'Media'),
        (PRIORIDAD_BAJA, 'Baja'),
    )

    propiedad = models.ForeignKey(
        Propiedad,
        on_delete=models.CASCADE,
        related_name='solicitudes_soporte',
    )
    reportado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitudes_soporte',
    )
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default=CATEGORIA_OTRO)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_NUEVA)
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default=PRIORIDAD_MEDIA)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'solicitud de soporte'
        verbose_name_plural = 'solicitudes de soporte'

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.propiedad.nombre}"

    @property
    def esta_abierta(self):
        return self.estado != self.ESTADO_RESUELTA


# ========== MÓDULOS DE CONTABILIDAD Y FINANZAS ==========

# ========== NÓMINA Y PERSONAL ==========

class PersonalEmpleado(models.Model):
    """
    Gestión de empleados (porteros, conserjes, personal de limpieza, jardineros)
    según regulaciones laborales colombianas 2024.
    """
    TIPOS_EMPLEADO = (
        ('PORTERO', 'Portero'),
        ('CONSERJE', 'Conserje'),
        ('LIMPIEZA', 'Personal de Limpieza'),
        ('JARDINERO', 'Jardinero'),
        ('SEGURIDAD', 'Personal de Seguridad'),
        ('OTRO', 'Otro'),
    )
    
    TIPOS_CONTRATO = (
        ('INDEFINIDO', 'Contrato Indefinido'),
        ('FIJO', 'Contrato a Término Fijo'),
        ('TEMPORAL', 'Contrato Temporal'),
    )

    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='empleados', null=True, blank=True)
    nombre_completo = models.CharField(max_length=200)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_empleado = models.CharField(max_length=20, choices=TIPOS_EMPLEADO)
    tipo_contrato = models.CharField(max_length=20, choices=TIPOS_CONTRATO, default='INDEFINIDO')
    
    salario_mensual_base = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Salario base en COP, sin deducciones'
    )
    fecha_inicio_contrato = models.DateField()
    fecha_fin_contrato = models.DateField(null=True, blank=True)
    correo = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['propiedad', 'tipo_empleado', 'nombre_completo']
        verbose_name = 'personal empleado'
        verbose_name_plural = 'personal empleados'

    def __str__(self):
        return f"{self.nombre_completo} - {self.get_tipo_empleado_display()}"


class NominaEmpleado(models.Model):
    """
    Registro mensual de nómina con cálculos automáticos según ley colombiana.
    SMMLV 2024: $1.600.000 COP
    """
    ESTADOS = (
        ('BORRADOR', 'Borrador'),
        ('CONFIRMADA', 'Confirmada'),
        ('PAGADA', 'Pagada'),
        ('CANCELADA', 'Cancelada'),
    )

    empleado = models.ForeignKey(PersonalEmpleado, on_delete=models.CASCADE, related_name='nominas')
    periodo_mes = models.DateField(help_text='Primer día del mes para el que se calcula')
    
    # Componentes básicos
    salario_base = models.DecimalField(max_digits=12, decimal_places=2)
    aux_transporte = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Auxilio de transporte (2024: $162.000)'
    )
    otros_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    horas_extras_100 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Horas extras al 25%'
    )
    horas_extras_150 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Horas extras nocturnas al 75%'
    )
    
    # Deducciones obligatorias (calculadas automáticamente)
    descuento_pension = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Aporte pension empleado: 4%'
    )
    descuento_salud = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Aporte salud: 4%'
    )
    descuento_fondo_solidaridad = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Fondo solidaridad pensional: 1% si salario > 4 SMMLV'
    )
    retenciones = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Retenciones en la fuente (si aplica)'
    )
    otros_descuentos = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Otros descuentos (préstamos, etc.)'
    )
    
    total_descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_devengado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Obligaciones del empleador
    aporte_pension_patronal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Aporte patrón a pensión: 12%'
    )
    aporte_arl = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Seguro de riesgo laboral (varía por actividad)'
    )
    aporte_sena = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='SENA: 2% (sobre nómina)'
    )
    aporte_icbf = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='ICBF: 3% (sobre nómina)'
    )
    aporte_cajaComp = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Caja de Compensación: 4% (sobre nómina)'
    )
    total_aportes_patronales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Control
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    fecha_pago = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True)
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-periodo_mes', 'empleado']
        unique_together = ['empleado', 'periodo_mes']
        verbose_name = 'nómina de empleado'
        verbose_name_plural = 'nóminas de empleados'

    def __str__(self):
        return f"Nómina {self.empleado.nombre_completo} - {self.periodo_mes.strftime('%m/%Y')}"

    def calcular_deducciones_y_aportes(self):
        """Calcula automáticamente todas las deducciones según ley colombiana."""
        from decimal import Decimal
        
        # Ingreso total
        ingreso_total = self.salario_base + self.aux_transporte + self.otros_ingresos
        ingreso_total += self.horas_extras_100 + self.horas_extras_150
        
        # Deducciones obligatorias del empleado
        self.descuento_pension = (self.salario_base * Decimal('0.04')).quantize(Decimal('0.01'))
        self.descuento_salud = (self.salario_base * Decimal('0.04')).quantize(Decimal('0.01'))
        
        # Fondo de solidaridad (solo si salario > 4 SMMLV = $6.400.000)
        if self.salario_base > Decimal('6400000'):
            excedente = self.salario_base - Decimal('6400000')
            self.descuento_fondo_solidaridad = (excedente * Decimal('0.01')).quantize(Decimal('0.01'))
        
        self.total_descuentos = (
            self.descuento_pension + self.descuento_salud + self.descuento_fondo_solidaridad +
            self.retenciones + self.otros_descuentos
        )
        
        self.total_devengado = ingreso_total
        self.total_neto = ingreso_total - self.total_descuentos
        
        # Aportes patronales
        self.aporte_pension_patronal = (self.salario_base * Decimal('0.12')).quantize(Decimal('0.01'))
        self.aporte_arl = (self.salario_base * Decimal('0.0522')).quantize(Decimal('0.01'))  # Promedio
        self.aporte_sena = (self.salario_base * Decimal('0.02')).quantize(Decimal('0.01'))
        self.aporte_icbf = (self.salario_base * Decimal('0.03')).quantize(Decimal('0.01'))
        self.aporte_cajaComp = (self.salario_base * Decimal('0.04')).quantize(Decimal('0.01'))
        
        self.total_aportes_patronales = (
            self.aporte_pension_patronal + self.aporte_arl +
            self.aporte_sena + self.aporte_icbf + self.aporte_cajaComp
        )
        
        return self


class EquiposUniformes(models.Model):
    """Registro y asignación de equipos y uniformes a empleados."""
    CATEGORIAS = (
        ('UNIFORME', 'Uniforme'),
        ('EQUIPO_SEGURIDAD', 'Equipo de Seguridad'),
        ('HERRAMIENTA', 'Herramienta'),
        ('OTRO', 'Otro'),
    )

    empleado = models.ForeignKey(PersonalEmpleado, on_delete=models.CASCADE, related_name='equipos')
    categoria = models.CharField(max_length=30, choices=CATEGORIAS)
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=1)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    
    fecha_asignacion = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
    
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.descripcion} - {self.empleado.nombre_completo}"

    @property
    def costo_total(self):
        return self.cantidad * self.costo_unitario


# ========== IMPUESTOS Y OBLIGACIONES FISCALES ==========

class ObligacionFiscal(models.Model):
    """
    Registro de obligaciones fiscales (impuestos, seguros, tarifas municipales)
    según regulaciones colombianas vigentes.
    """
    TIPOS_OBLIGACION = (
        ('IMPUESTO_PREDIAL', 'Impuesto Predial'),
        ('SEGURO_INCENDIO', 'Seguro Obligatorio - Incendios'),
        ('SEGURO_TERREMOTO', 'Seguro Obligatorio - Terremoto'),
        ('ACUEDUCTO', 'Acueducto y Alcantarillado'),
        ('ENERGIA', 'Servicio de Energía Eléctrica'),
        ('GAS', 'Servicio de Gas'),
        ('RECOLECCION', 'Recolección de Basura'),
        ('ALUMBRADO', 'Alumbrado Público'),
        ('OTRO_IMPUESTO', 'Otro Impuesto/Tarifa'),
    )
    
    FRECUENCIAS_PAGO = (
        ('MENSUAL', 'Mensual'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
        ('UNICA', 'Única'),
    )

    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='obligaciones_fiscales')
    tipo_obligacion = models.CharField(max_length=30, choices=TIPOS_OBLIGACION)
    descripcion = models.CharField(max_length=200, blank=True)
    
    monto_obligacion = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monto estimado en COP'
    )
    frecuencia_pago = models.CharField(max_length=20, choices=FRECUENCIAS_PAGO)
    
    # Fechas de pago
    fecha_vencimiento_proximo = models.DateField()
    dias_alerta = models.PositiveIntegerField(
        default=15,
        help_text='Días antes del vencimiento para mostrar alerta'
    )
    
    referencia_externa = models.CharField(max_length=100, blank=True, help_text='Número de referencia, cuenta o código')
    
    activa = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_vencimiento_proximo', 'propiedad']
        
    def __str__(self):
        return f"{self.get_tipo_obligacion_display()} - {self.propiedad.nombre}"

    @property
    def esta_vencida(self):
        from datetime import date
        return self.fecha_vencimiento_proximo < date.today()

    @property
    def dias_para_vencer(self):
        from datetime import date
        delta = (self.fecha_vencimiento_proximo - date.today()).days
        return max(0, delta)

    @property
    def requiere_alerta(self):
        return self.dias_para_vencer <= self.dias_alerta and not self.esta_vencida


class PagoObligacion(models.Model):
    """Registro detallado de pagos de obligaciones fiscales."""
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('SOBRE_PAGO', 'Sobre Pago'),
        ('SIN_PODER', 'Sin Poder Pagar'),
    )

    obligacion = models.ForeignKey(ObligacionFiscal, on_delete=models.CASCADE, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField()
    fecha_vencimiento_original = models.DateField()
    
    metodo_pago = models.CharField(
        max_length=50, blank=True,
        help_text='Ej: Transferencia, efectivo, ACH, etc.'
    )
    referencia_pago = models.CharField(max_length=100, blank=True, help_text='Comp. bancario, recibo, etc.')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PAGADO')
    
    notas = models.TextField(blank=True)
    
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.obligacion.get_tipo_obligacion_display()} - {self.fecha_pago}"

    @property
    def dias_atraso(self):
        delta = (self.fecha_pago - self.fecha_vencimiento_original).days
        return max(0, delta)


# ========== SERVICIOS DE MANTENIMIENTO CONTRATADO ==========

class ContratoMantenimiento(models.Model):
    """
    Contratos de mantenimiento para servicios recurrentes:
    Ascensores, seguridad electrónica, software, etc.
    """
    TIPOS_SERVICIO = (
        ('ASCENSORES', 'Mantenimiento de Ascensores'),
        ('SEGURIDAD_ELECTRONICA', 'Sistemas de Seguridad Electrónica'),
        ('CAMARAS', 'Monitoreo de Cámaras'),
        ('ALARMAS', 'Sistemas de Alarma'),
        ('CERCAS_ELECTRICAS', 'Cercas Eléctricas'),
        ('SOFTWARE', 'Licencias de Software'),
        ('ASESORIA_CONTABLE', 'Asesoría Contable'),
        ('ASESORIA_LEGAL', 'Asesoría Legal'),
        ('OTRO_SERVICIO', 'Otro Servicio'),
    )
    
    ESTADOS = (
        ('ACTIVO', 'Activo'),
        ('SUSPENDIDO', 'Suspendido'),
        ('EXPIRADO', 'Expirado'),
        ('CANCELADO', 'Cancelado'),
    )

    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='contratos_mantenimiento')
    tipo_servicio = models.CharField(max_length=30, choices=TIPOS_SERVICIO)
    proveedor = models.CharField(max_length=200)
    
    costo_mensual = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Costo mensual en COP'
    )
    
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_proximo_pago = models.DateField()
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVO')
    
    telefono_proveedor = models.CharField(max_length=20, blank=True)
    correo_proveedor = models.EmailField(blank=True)
    numero_contrato = models.CharField(max_length=100, blank=True)
    
    alerta_renovacion_dias = models.PositiveIntegerField(
        default=30,
        help_text='Días antes del fin para alertar renovación'
    )
    
    notas = models.TextField(blank=True)
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_proximo_pago', 'propiedad']

    def __str__(self):
        return f"{self.get_tipo_servicio_display()} - {self.proveedor}"

    @property
    def esta_vencido(self):
        if not self.fecha_fin:
            return False
        from datetime import date
        return self.fecha_fin < date.today()

    @property
    def requiere_renovacion(self):
        if not self.fecha_fin:
            return False
        from datetime import date, timedelta
        fecha_alerta = self.fecha_fin - timedelta(days=self.alerta_renovacion_dias)
        return date.today() >= fecha_alerta and not self.esta_vencido


class PagoMantenimiento(models.Model):
    """Registro de pagos mensuales de contratos de mantenimiento."""
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('PROCESANDO', 'En Proceso'),
        ('CANCELADO', 'Cancelado'),
    )

    contrato = models.ForeignKey(ContratoMantenimiento, on_delete=models.CASCADE, related_name='pagos')
    periodo_mes = models.DateField(help_text='Primer día del mes')
    
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    fecha_pago = models.DateField(null=True, blank=True)
    comprobante_pago = models.CharField(max_length=100, blank=True)
    
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-periodo_mes']
        unique_together = ['contrato', 'periodo_mes']

    def __str__(self):
        return f"Pago {self.contrato.proveedor} - {self.periodo_mes.strftime('%m/%Y')}"


# ========== SERVICIOS PÚBLICOS DE ÁREAS COMUNES ==========

class GastoServicioPublico(models.Model):
    """
    Rastreo de gastos en servicios públicos para áreas comunes:
    Electricidad, agua, gas, internet, telefonía.
    """
    TIPOS_SERVICIO = (
        ('ELECTRICIDAD_AREAS_COMUNES', 'Electricidad - Áreas Comunes'),
        ('ELECTRICIDAD_BOMBAS', 'Electricidad - Bombas de Agua'),
        ('ELECTRICIDAD_ASCENSORES', 'Electricidad - Ascensores'),
        ('AGUA_RIEGO', 'Agua - Riego de Áreas Verdes'),
        ('AGUA_LIMPIEZA', 'Agua - Limpieza de Áreas Comunes'),
        ('GAS_AREAS_COMUNES', 'Gas - Áreas Comunes'),
        ('INTERNET_TELEFONÍA', 'Internet / Telefonía'),
        ('OTRO_SERVICIO_PUBLICO', 'Otro Servicio'),
    )
    
    UNIDADES_MEDIDA = (
        ('KWH', 'kWh - Electricidad'),
        ('M3', 'm³ - Metros Cúbicos'),
        ('GLOBAL', 'Tarifa Global'),
        ('OTROS', 'Otros'),
    )

    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='gastos_servicios_publicos')
    tipo_servicio = models.CharField(max_length=40, choices=TIPOS_SERVICIO)
    
    # Información del período
    periodo_mes = models.DateField(help_text='Mes del gasto')
    
    # Medición real o estimación
    cantidad_consumida = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Consumo real si está disponible'
    )
    unidad_medida = models.CharField(
        max_length=20, choices=UNIDADES_MEDIDA, default='KWH'
    )
    
    tarifa_unitaria = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text='Precio unitario'
    )
    
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Costo total en COP'
    )
    
    es_estimacion = models.BooleanField(
        default=False,
        help_text='Marcar si es presupuesto y no consumo real'
    )
    
    factura_numero = models.CharField(max_length=100, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    
    notas = models.TextField(blank=True)
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-periodo_mes', 'tipo_servicio']
        unique_together = ['propiedad', 'tipo_servicio', 'periodo_mes']

    def __str__(self):
        return f"{self.get_tipo_servicio_display()} - {self.propiedad.nombre}"


# ========== REPORTES Y CONSOLIDADOS ==========

class ReporteContableMensual(models.Model):
    """
    Resumen consolidado mensual de todos los gastos operacionales.
    Generado automáticamente para facilitar análisis.
    """
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='reportes_contables')
    periodo_mes = models.DateField(help_text='Primer día del mes')
    
    # Nómina
    total_salarios_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deducciones_empleados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_neto_nómina = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_aportes_patronales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_equipos_uniformes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_personal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Impuestos y obligaciones
    total_obligaciones_fiscales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Mantenimiento
    total_mantenimiento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Servicios públicos
    total_servicios_publicos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Consolidado
    total_gastos_operacionales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Desglose de servicios
    detalle_electricidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    detalle_agua = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    detalle_gas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    detalle_internet = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Auditoría
    generado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-periodo_mes', 'propiedad']
        unique_together = ['propiedad', 'periodo_mes']

    def __str__(self):
        return f"Reporte {self.propiedad.nombre} - {self.periodo_mes.strftime('%m/%Y')}"
