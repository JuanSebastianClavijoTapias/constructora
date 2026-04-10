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
