# Permisos y Control de Acceso - Módulo de Contabilidad

## 🔐 Reglas de Acceso

### Restricciones de Acceso a Contabilidad

**SOLO los administradores pueden acceder al módulo de contabilidad.**

#### Nivel 1: Decorador en Función
Todas las vistas de contabilidad tienen `@admin_required` que verifica:
- ✅ Usuario debe estar autenticado (`@login_required`)
- ✅ Usuario debe tener `profile.es_admin = True`
- ✅ Usuario debe tener acceso a la propiedad (si aplica)

#### Nivel 2: Validación Adicional en Funciones Críticas
Funciones sensibles tienen validaciones adicionales:
- `pago_obligacion_registrar()` - Verifica acceso a propiedad
- `reporte_excel()` - Verifica estado de usuario activo
- `reporte_pdf()` - Verifica estado de usuario activo
- `nomina_excel()` - Verifica estado de usuario activo
- `obligaciones_excel()` - Verifica estado de usuario activo

#### Nivel 3: Control de Propiedades
Solo admins pueden ver/acceder a todas las propiedades:
- Admins: acceso a todas las propiedades
- Otros usuarios: solo su propiedad asignada
- Para contabilidad: solo admins, sin restricción de propiedad

## 📋 Funciones Protegidas

### CRUD de Empleados
- ✅ `empleados_lista()` - @admin_required
- ✅ `empleado_crear()` - @admin_required  
- ✅ `empleado_editar()` - @admin_required
- ✅ `empleado_detalle()` - @admin_required

### CRUD de Nóminas
- ✅ `nomina_lista()` - @admin_required
- ✅ `nomina_crear()` - @admin_required
- ✅ `nomina_detalle()` - @admin_required

### CRUD de Obligaciones Fiscales
- ✅ `obligaciones_fiscales_lista()` - @admin_required
- ✅ `obligacion_crear()` - @admin_required
- ✅ `obligacion_editar()` - @admin_required
- ✅ `pago_obligacion_registrar()` - @admin_required + validación propiedad

### CRUD de Contratos
- ✅ `contratos_mantenimiento_lista()` - @admin_required
- ✅ `contrato_crear()` - @admin_required
- ✅ `contrato_editar()` - @admin_required

### CRUD de Servicios Públicos
- ✅ `servicios_publicos_lista()` - @admin_required
- ✅ `servicio_publico_crear()` - @admin_required

### Reportes y Exportación
- ✅ `contabilidad_dashboard()` - @admin_required
- ✅ `reporte_mensual()` - @admin_required
- ✅ `reporte_anual()` - @admin_required
- ✅ `tendencias_financieras()` - @admin_required
- ✅ `reporte_excel()` - @admin_required + validación usuario activo
- ✅ `reporte_pdf()` - @admin_required + validación usuario activo
- ✅ `nomina_excel()` - @admin_required + validación usuario activo
- ✅ `obligaciones_excel()` - @admin_required + validación usuario activo

## 🔄 Flujo de Autenticación

```
1. Usuario intenta acceder a /contabilidad/
   ↓
2. Django ejecuta @login_required
   ├─ NO autenticado → redirect a login
   └─ Autenticado → continúa
   ↓
3. Django ejecuta @admin_required
   ├─ profile.es_admin = False → error + redirect dashboard
   ├─ No tiene acceso a propiedad → error + redirect dashboard
   └─ Es admin → continúa
   ↓
4. (Si función crítica) Validación adicional
   ├─ Usuario no activo → error + redirect
   └─ Usuario activo → ejecuta función
   ↓
5. Vista presenta datos y renderiza template
```

## 🛡️ Seguridad Implementada

### Decorador `@admin_required`
```python
def admin_required(view_func):
    """
    Verifica:
    - Usuario autenticado
    - profile.es_admin = True
    - Acceso a propiedad (si aplica)
    """
```

### Decorador `@contabilidad_required` (disponible para uso futuro)
```python
def contabilidad_required(view_func):
    """
    Versión más restrictiva:
    - Todas las verificaciones de @admin_required
    - Usuario.is_active = True
    - Log de auditoría
    """
```

### Validaciones en Funciones Críticas
```python
# En reporte_excel, nomina_excel, etc.
if not (profile.es_admin and request.user.is_active):
    messages.error(request, 'No tienes autorización...')
    return redirect('dashboard')
```

## 📝 Pruebas Recomendadas

```bash
# Verificar que no-admin no puede acceder
curl -H "Authorization: Bearer <token_no_admin>" http://localhost:8000/contabilidad/

# Verificar que admin SÍ puede acceder
curl -H "Authorization: Bearer <token_admin>" http://localhost:8000/contabilidad/

# Verificar exportaciones protegidas
curl http://localhost:8000/contabilidad/reporte/excel/
# Debe redirigir a login si no autenticado
# Debe mostrar error si no es admin
```

## 🔐 Mejores Prácticas

1. **Nunca confies en el cliente**: Toda validación debe estar en el servidor
2. **Validar en múltiples niveles**: decorador + función + querysets
3. **Auditar accesos**: Loguear accesos a datos sensibles
4. **Filtrar querysets**: Usar `filter()` por propiedad incluso con admin
5. **Session timeout**: Implementar timeout de sesión para datos sensibles

## 📌 Notas

- Los admins NO están restringidos por propiedad en contabilidad
- Todos los accesos deben estar autenticados
- Los usuarios no-admin no ven links de contabilidad (en base.html)
- Las exportaciones no funcionan para usuarios no-admin
