from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pagos/', views.pagos, name='pagos'),
    path('soporte/', views.soporte, name='soporte'),
    path('propiedades/', views.propiedades, name='propiedades'),
    path('propiedades/crear/', views.propiedad_crear, name='propiedad_crear'),
    path('propiedades/<int:pk>/editar/', views.propiedad_editar, name='propiedad_editar'),
    path('pagos/crear/', views.pago_crear, name='pago_crear'),
    path('pagos/<int:pk>/editar/', views.pago_editar, name='pago_editar'),
]
