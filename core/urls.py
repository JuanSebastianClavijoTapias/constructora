from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.setup, name='setup'),
    path('login/', views.login_view, name='login'),
    path('salir/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('pagos/', views.pagos, name='pagos'),
    path('soporte/', views.soporte, name='soporte'),
    path('soporte/quick/', views.soporte_crear_rapido, name='soporte_crear_rapido'),
    path('soporte/custom/', views.soporte_crear_personalizado, name='soporte_crear_personalizado'),
    path('soporte/<int:pk>/estado/', views.soporte_actualizar_estado, name='soporte_actualizar_estado'),
    path('propiedades/', views.propiedades, name='propiedades'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('propiedades/crear/', views.propiedad_crear, name='propiedad_crear'),
    path('propiedades/<int:pk>/editar/', views.propiedad_editar, name='propiedad_editar'),
    path('pagos/crear/', views.pago_crear, name='pago_crear'),
    path('pagos/<int:pk>/editar/', views.pago_editar, name='pago_editar'),
]
