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
    
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='pagos')
    inquilino_nombre = models.CharField(max_length=150)
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_limite = models.DateField()
    metodo_pago = models.CharField(max_length=100, blank=True, null=True)
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
