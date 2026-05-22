from django.urls import path
from . import views
from . import accounting_views

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
    path('propiedades/<int:pk>/', views.propiedad_detalle, name='propiedad_detalle'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('propiedades/crear/', views.propiedad_crear, name='propiedad_crear'),
    path('propiedades/<int:pk>/editar/', views.propiedad_editar, name='propiedad_editar'),
    path('pagos/crear/', views.pago_crear, name='pago_crear'),
    path('pagos/<int:pk>/editar/', views.pago_editar, name='pago_editar'),
    
    # ========== RUTAS DE CONTABILIDAD ==========
    
    # Dashboard de contabilidad
    path('contabilidad/', accounting_views.contabilidad_dashboard, name='contabilidad_dashboard'),
    
    # Empleados
    path('contabilidad/empleados/', accounting_views.empleados_lista, name='empleados_lista'),
    path('contabilidad/empleados/crear/', accounting_views.empleado_crear, name='empleado_crear'),
    path('contabilidad/empleados/<int:pk>/editar/', accounting_views.empleado_editar, name='empleado_editar'),
    path('contabilidad/empleados/<int:pk>/detalle/', accounting_views.empleado_detalle, name='empleado_detalle'),
    path('contabilidad/empleados/propiedad/<int:propiedad_id>/', accounting_views.empleados_lista, name='empleados_lista_propiedad'),
    path('contabilidad/empleados/crear/<int:propiedad_id>/', accounting_views.empleado_crear, name='empleado_crear_propiedad'),
    
    # Nómina
    path('contabilidad/nomina/', accounting_views.nomina_lista, name='nomina_lista'),
    path('contabilidad/nomina/crear/<int:empleado_id>/', accounting_views.nomina_crear, name='nomina_crear'),
    path('contabilidad/nomina/<int:pk>/detalle/', accounting_views.nomina_detalle, name='nomina_detalle'),
    path('contabilidad/nomina/<int:pk>/pagar/', accounting_views.nomina_pagar, name='nomina_pagar'),
    path('contabilidad/nomina/propiedad/<int:propiedad_id>/', accounting_views.nomina_lista, name='nomina_lista_propiedad'),
    
    # Obligaciones fiscales
    path('contabilidad/obligaciones/', accounting_views.obligaciones_fiscales_lista, name='obligaciones_fiscales_lista'),
    path('contabilidad/obligaciones/crear/', accounting_views.obligacion_crear, name='obligacion_crear'),
    path('contabilidad/obligaciones/<int:pk>/editar/', accounting_views.obligacion_editar, name='obligacion_editar'),
    path('contabilidad/obligaciones/<int:obligacion_id>/pago/', accounting_views.pago_obligacion_registrar, name='pago_obligacion_registrar'),
    path('contabilidad/obligaciones/propiedad/<int:propiedad_id>/', accounting_views.obligaciones_fiscales_lista, name='obligaciones_fiscales_lista_propiedad'),
    path('contabilidad/obligaciones/crear/<int:propiedad_id>/', accounting_views.obligacion_crear, name='obligacion_crear_propiedad'),
    
    # Contratos de mantenimiento
    path('contabilidad/mantenimiento/', accounting_views.contratos_mantenimiento_lista, name='contratos_mantenimiento_lista'),
    path('contabilidad/mantenimiento/crear/', accounting_views.contrato_crear, name='contrato_crear'),
    path('contabilidad/mantenimiento/<int:pk>/editar/', accounting_views.contrato_editar, name='contrato_editar'),
    path('contabilidad/mantenimiento/propiedad/<int:propiedad_id>/', accounting_views.contratos_mantenimiento_lista, name='contratos_mantenimiento_lista_propiedad'),
    path('contabilidad/mantenimiento/crear/<int:propiedad_id>/', accounting_views.contrato_crear, name='contrato_crear_propiedad'),
    
    # Servicios públicos
    path('contabilidad/servicios-publicos/', accounting_views.servicios_publicos_lista, name='servicios_publicos_lista'),
    path('contabilidad/servicios-publicos/crear/', accounting_views.servicio_publico_crear, name='servicio_publico_crear'),
    path('contabilidad/servicios-publicos/propiedad/<int:propiedad_id>/', accounting_views.servicios_publicos_lista, name='servicios_publicos_lista_propiedad'),
    path('contabilidad/servicios-publicos/crear/<int:propiedad_id>/', accounting_views.servicio_publico_crear, name='servicio_publico_crear_propiedad'),
    path('contabilidad/servicios-publicos/<int:pk>/editar/', accounting_views.servicio_publico_editar, name='servicio_publico_editar'),
    path('contabilidad/servicios-publicos/<int:pk>/eliminar/', accounting_views.servicio_publico_eliminar, name='servicio_publico_eliminar'),
    
    # Reportes
    path('contabilidad/reporte/mensual/<int:propiedad_id>/', accounting_views.reporte_mensual, name='reporte_mensual'),
    path('contabilidad/reporte/mensual/<int:propiedad_id>/<str:periodo_mes>/', accounting_views.reporte_mensual, name='reporte_mensual_fecha'),
    path('contabilidad/reporte/anual/<int:propiedad_id>/', accounting_views.reporte_anual, name='reporte_anual'),
    path('contabilidad/reporte/anual/<int:propiedad_id>/<int:año>/', accounting_views.reporte_anual, name='reporte_anual_año'),
    path('contabilidad/tendencias/<int:propiedad_id>/', accounting_views.tendencias_financieras, name='tendencias_financieras'),
    
    # Exportación a Excel y PDF
    path('contabilidad/reporte/excel/', accounting_views.reporte_excel, name='reporte_excel'),
    path('contabilidad/reporte/excel/<int:mes>/<int:anio>/', accounting_views.reporte_excel, name='reporte_excel_fecha'),
    path('contabilidad/reporte/pdf/', accounting_views.reporte_pdf, name='reporte_pdf'),
    path('contabilidad/reporte/pdf/<int:mes>/<int:anio>/', accounting_views.reporte_pdf, name='reporte_pdf_fecha'),
    path('contabilidad/nomina/excel/', accounting_views.nomina_excel, name='nomina_excel'),
    path('contabilidad/obligaciones/excel/', accounting_views.obligaciones_excel, name='obligaciones_excel'),
]
