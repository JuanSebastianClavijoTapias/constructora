from django.contrib import admin

from .models import Pago, PerfilUsuario, Propiedad, PropiedadImagen, SolicitudSoporte


class PropiedadImagenInline(admin.TabularInline):
	model = PropiedadImagen
	extra = 0


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'direccion', 'estado', 'precio_mensual', 'inquilino_nombre')
	search_fields = ('nombre', 'direccion', 'inquilino_nombre')
	list_filter = ('estado',)
	inlines = [PropiedadImagenInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
	list_display = ('inquilino_nombre', 'propiedad', 'monto_mensual', 'fecha_limite', 'estado')
	search_fields = ('inquilino_nombre', 'propiedad__nombre')
	list_filter = ('estado', 'fecha_limite')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
	list_display = ('user', 'rol', 'propiedad', 'telefono', 'creado_en')
	search_fields = ('user__username', 'user__first_name', 'user__last_name', 'propiedad__nombre')
	list_filter = ('rol',)


@admin.register(SolicitudSoporte)
class SolicitudSoporteAdmin(admin.ModelAdmin):
	list_display = ('titulo', 'propiedad', 'reportado_por', 'categoria', 'prioridad', 'estado', 'creado_en')
	search_fields = ('titulo', 'propiedad__nombre', 'reportado_por__username')
	list_filter = ('estado', 'prioridad', 'categoria')
