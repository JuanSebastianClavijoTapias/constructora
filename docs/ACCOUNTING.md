# Documentación Técnica - Sistema de Contabilidad y Finanzas para Administración de Propiedades en Colombia

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Regulaciones Implementadas](#regulaciones-implementadas)
4. [Módulos del Sistema](#módulos-del-sistema)
5. [Guía de Uso](#guía-de-uso)
6. [Referencia Técnica](#referencia-técnica)
7. [Cálculos de Nómina](#cálculos-de-nómina)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de contabilidad proporciona un sistema completo e integrado para la gestión financiera de propiedades residenciales y comerciales en Colombia, cumpliendo con todas las regulaciones fiscales y laborales vigentes en 2024.

**Características principales:**
- Gestión de nómina con cálculos automáticos según ley colombiana
- Rastreo de obligaciones fiscales con alertas de vencimiento
- Contratos de servicios de mantenimiento
- Monitoreo de servicios públicos (electricidad, agua, gas, internet)
- Reportes consolidados mensuales y anuales
- Análisis de tendencias financieras

**Requisitos:**
- Django 6.0.3+
- Python 3.8+
- python-dateutil

---

## Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install python-dateutil
```

### 2. Crear migraciones e inicializar BD

```bash
python manage.py migrate
```

### 3. Acceder al módulo

El sistema de contabilidad está disponible en:
```
/contabilidad/
```

**Permisos requeridos:** Solo administradores pueden acceder al módulo de contabilidad.

---

## Regulaciones Implementadas

### 1. Normas Laborales Colombia 2024

#### Salario Mínimo Mensual Legal Vigente (SMMLV)
- **Valor:** $1.600.000 COP
- **Auxilio de Transporte:** $162.000 COP (aplica para empleados con salario hasta 2 SMMLV)
- **Límite de Auxilio:** 2 × SMMLV = $3.200.000

### 2. Aportes Obligatorios del Empleado

| Concepto | Porcentaje | Base de Cálculo | Notas |
|----------|-----------|-----------------|-------|
| Aporte a Pensión | 4% | Salario base | Obligatorio |
| Aporte a Salud | 4% | Salario base | Obligatorio |
| Fondo de Solidaridad Pensional | 1% | Excedente > 4 SMMLV | Solo si salario > $6.400.000 |

**Fondo de Solidaridad:** Se calcula SOLO sobre la parte del salario que excede 4 SMMLV.
- Si salario ≤ $6.400.000: No aplica
- Si salario > $6.400.000: 1% del excedente

### 3. Aportes Obligatorios del Empleador

| Concepto | Porcentaje | Base | Notas |
|----------|-----------|------|-------|
| Aporte a Pensión | 12% | Nómina | Obligatorio |
| Aporte a Salud | 8.5% | Nómina | Promedio (varía por entidad) |
| SENA | 2% | Nómina | Obligatorio |
| ICBF | 3% | Nómina | Obligatorio |
| Caja de Compensación | 4% | Nómina | Obligatorio |
| ARL (Riesgo Laboral) | Variable | Nómina | Ver tabla de riesgos |

### 4. Tasas de ARL (Seguro de Riesgo Laboral) 2024

Por tipo de empleado en edificios residenciales:

| Tipo de Empleado | Categoría de Riesgo | Tasa Aproximada |
|-----------------|-------------------|-----------------|
| Portero | Bajo | 1.00% |
| Conserje | Bajo | 1.04% |
| Personal de Limpieza | Moderado | 1.52% |
| Jardinero | Moderado-Alto | 2.54% |
| Personal de Seguridad | Alto | 6.76% |

**Nota:** Las tasas de ARL varían según la clasificación industrial de riesgo. Las tasas anteriores son aproximaciones para edificios residenciales/comerciales.

### 5. Obligaciones Fiscales Principales

#### Impuesto Predial
- Recaudador: Municipalidad
- Frecuencia: Anual (generalmente enero-marzo)
- Base: Avalúo catastral actualizado

#### Seguros Obligatorios
- **Incendios:** Póliza anual obligatoria
- **Terremoto:** Póliza anual obligatoria (algunas municipalidades)

#### Servicios Municipales
- Recolección de basura
- Alumbrado público
- Acueducto y alcantarillado
- Aseo de vías

### 6. Retención en la Fuente 2024

Se calcula automáticamente según UVT ($43.348):

| Rango | Tarifa | Observación |
|-------|--------|-------------|
| Hasta 95 UVT (~$4.118.060) | 0% | No aplica |
| 95 - 150 UVT | 5% | Sobre excedente |
| Mayor a 150 UVT | 19% | Progresivo |

**Nota:** Para empleados de servicios (porteros, conserjes, limpieza), típicamente no aplica retención.

---

## Módulos del Sistema

### 1. Gestión de Empleados

**Ubicación:** `/contabilidad/empleados/`

**Funcionalidades:**
- Registrar empleados (porteros, conserjes, personal de limpieza, jardineros)
- Tipos de contrato: Indefinido, Fijo o Temporal
- Información de contacto
- Historial de nómina por empleado

**Campos principales:**
- Nombre completo
- Cédula (única, no se permiten duplicados)
- Tipo de empleado
- Tipo de contrato
- Salario mensual base
- Fechas de contrato
- Estado (Activo/Inactivo)

### 2. Gestión de Nómina

**Ubicación:** `/contabilidad/nomina/`

**Funcionalidades:**
- Crear nóminas mensuales
- Cálculos automáticos de deducciones
- Visualización de aportes patronales
- Desglose completo de ingresos y descuentos
- Estados: Borrador → Confirmada → Pagada

**Cálculos automáticos:**
- Deducciones (pensión, salud, fondo solidaridad)
- Aportes patronales (pensión, salud, SENA, ICBF, Caja)
- Total neto del empleado
- Costo total para empleador (neto + aportes)

**Componentes de ingresos:**
- Salario base
- Auxilio de transporte
- Horas extras (100% y 150%)
- Otros ingresos

**Componentes de descuentos:**
- Deducciones obligatorias
- Retenciones en la fuente
- Otros descuentos (préstamos internos, etc.)

### 3. Obligaciones Fiscales

**Ubicación:** `/contabilidad/obligaciones/`

**Funcionalidades:**
- Registrar todas las obligaciones fiscales o financieras
- Alertas automáticas de vencimiento (configurable)
- Registro de pagos
- Actualización automática de próxima fecha de vencimiento

**Tipos de obligaciones:**
- Impuesto predial
- Seguros obligatorios (incendios, terremoto)
- Servicios municipales
- Impuestos de servicios

**Campos configurables:**
- Monto de la obligación
- Frecuencia de pago (mensual, trimestral, semestral, anual)
- Días de alerta antes del vencimiento
- Referencia externa (código de cuenta)

### 4. Contratos de Mantenimiento

**Ubicación:** `/contabilidad/mantenimiento/`

**Funcionalidades:**
- Registrar contratos recurrentes (ascensores, seguridad, software)
- Seguimiento de estados (Activo, Suspendido, Expirado)
- Alertas de renovación
- Registro de pagos mensuales

**Tipos de servicios:**
- Mantenimiento de ascensores
- Sistemas de seguridad electrónica
- Monitoreo de cámaras
- Alarmas
- Cercas eléctricas
- Software / Licencias
- Asesorías (contable, legal)

### 5. Servicios Públicos

**Ubicación:** `/contabilidad/servicios-publicos/`

**Funcionalidades:**
- Registrar consumo mensual o estimaciones
- Múltiples categorías de servicios
- Seguimiento histó rico de tendencias

**Servicios:**
- Electricidad (áreas comunes, bombas, ascensores)
- Agua (riego, limpieza)
- Gas
- Internet/Telefonía

### 6. Reportes y Análisis

**Ubicación:** `/contabilidad/reporte/`

#### Reporte Mensual
Consolidado completo de gastos del mes:
- Total de nómina (salarios + aportes)
- Obligaciones fiscales
- Mantenimiento
- Servicios públicos
- Desglose por categoría de servicio

#### Reporte Anual
Comparativa anual con:
- Resumen mensual de gastos
- Mes con mayor gasto
- Tendencias

#### Análisis de Tendencias
- Comparativa últimos 3 meses
- Tendencia (incremento/decremento)
- Gastos proyectados para próximos 30 días

---

## Guía de Uso

### A. Crear un Nuevo Empleado

1. Ir a **Contabilidad** → **Empleados** → **Agregar Empleado**
2. Completar el formulario:
   - Nombre completo
   - Cédula (sin puntos ni guiones)
   - Tipo de empleado (Portero, Conserje, Limpieza, Jardinero, etc.)
   - Salario mensual base
   - Seleccionar propiedad
3. Hacer clic en **Guardar**

**Recomendaciones:**
- Usar números de cédula exactos para auditoría
- El salario base debe ser ≥ SMMLV 2024 ($1.600.000)
- Se marca automáticamente como "Activo"

### B. Crear Nómina Mensual

1. Ir a **Contabilidad** → **Nómina** → **Crear Nómina**
2. Seleccionar empleado
3. Ingresar período (siempre el 1º del mes)
4. Ingresar componentes:
   - Salario base (pre-llenado)
   - Auxilio de transporte ($162.000 si aplica)
   - Horas extras (si aplica)
5. El sistema calcula automáticamente:
   - Deducciones
   - Aportes patronales
   - Total neto
6. Hacer clic en **Guardar** o **Guardar como Confirmada**

**Importante:**
- Los cálculos se realizan automáticamente
- No es necesario ingresar deducciones manualmente
- Revisar el desglose antes de confirmar

### C. Registrar Obligación Fiscal

1. Ir a **Contabilidad** → **Obligaciones Fiscales** → **Nueva**
2. Seleccionar tipo de obligación
3. Ingresar:
   - Monto
   - Frecuencia de pago
   - Fecha de próximo vencimiento
   - Días de alerta (recomendado: 15-20 días)
4. Guardar

**Ejemplo - Impuesto Predial:**
- Tipo: Impuesto Predial
- Monto: $500.000
- Frecuencia: Anual
- Próximo vencimiento: 31-05-2024
- Alerta: 30 días antes

### D. Registrar Pago de Obligación

1. Desde listado de obligaciones, buscar la pendiente
2. Hacer clic en **Registrar Pago**
3. Ingresar:
   - Monto pagado
   - Fecha del pago
   - Método (transferencia, efectivo, etc.)
   - Referencia/Comprobante
4. El sistema actualiza automáticamente la próxima fecha de vencimiento

### E. Crear Contrato de Mantenimiento

1. Ir a **Contabilidad** → **Mantenimiento** → **Nuevo Contrato**
2. Completar:
   - Tipo de servicio
   - Proveedor
   - Costo mensual
   - Fechas de vigencia
   - Datos de contacto (opcional)
3. Guardar

**Alertas automáticas:**
- El sistema alerta si falta <30 días para vencimiento

### F. Registrar Gasto de Servicio Público

1. Ir a **Contabilidad** → **Servicios Públicos** → **Nuevo**
2. Seleccionar:
   - Tipo de servicio (Electricidad, Agua, etc.)
   - Período
   - Monto total
3. Opcionalmente:
   - Ingresar consumo y tarifa unitaria
   - Marcar si es estimación
4. Guardar

### G. Generar Reporte Mensual

1. Ir a **Contabilidad** → **Reportes** → **Mensual**
2. Seleccionar propiedad y período
3. El sistema genera automáticamente:
   - Consolidado de nómina
   - Obligaciones pagadas
   - Servicios
   - Total de gastos
4. Opción de descargar o imprimir

---

## Referencia Técnica

### Estructura de Modelos

```
PersonalEmpleado
├── propiedad (FK)
├── información personal
├── contrato
└── nominas (reverse FK)

NominaEmpleado
├── empleado (FK)
├── período, ingresos
├── deducciones (auto-calculadas)
├── aportes_patronales (auto-calculados)
└── estado

ObligacionFiscal
├── propiedad (FK)
├── tipo, monto, frecuencia
├── vencimiento
├── pagos (reverse FK)
└── alertas

ContratoMantenimiento
├── propiedad (FK)
├── proveedor, servicios
├── fechas, costos
└── pagos (reverse FK)

GastoServicioPublico
├── propiedad (FK)
├── tipo de servicio
├── período, monto
└── información de factura

ReporteContableMensual
├── propiedad (FK)
├── período
├── consolidados de cada módulo
└── totales finales
```

### Constantes del Sistema

**Ubicación:** `core/accounting.py`

```python
class ConstantesColombiana2024:
    SMMLV = Decimal('1600000')
    AUXILIO_TRANSPORTE = Decimal('162000')
    APORTE_PENSION_EMPLEADO = Decimal('0.04')  # 4%
    APORTE_SALUD_EMPLEADO = Decimal('0.04')    # 4%
    APORTE_PENSION_EMPLEADOR = Decimal('0.12') # 12%
    # ... más constantes
```

### Funciones de Cálculo

**Nómina:**
```python
calculador = CalculadoraNomina()
nomina = calculador.calcular_nomina_completa(nomina)
```

**Reportes:**
```python
reporte = GeneradorReportesContables.generar_reporte_mensual(propiedad, periodo)
```

### URLs Principales

| Función | URL | Parámetros |
|---------|-----|-----------|
| Dashboard | `/contabilidad/` | - |
| Empleados | `/contabilidad/empleados/` | propiedad_id (opt) |
| Nómina | `/contabilidad/nomina/` | propiedad_id (opt) |
| Obligaciones | `/contabilidad/obligaciones/` | propiedad_id (opt) |
| Mantenimiento | `/contabilidad/mantenimiento/` | propiedad_id (opt) |
| Servicios | `/contabilidad/servicios-publicos/` | propiedad_id (opt) |
| Reporte Mensual | `/contabilidad/reporte/mensual/<id>/` | periodo_mes (opt) |
| Reporte Anual | `/contabilidad/reporte/anual/<id>/` | año (opt) |

---

## Cálculos de Nómina

### Fórmula de Cálculo Completa

#### 1. Ingresos

```
Total Ingresos = Salario Base + Auxilio Transporte + Horas Extras + Otros Ingresos
```

#### 2. Deducciones del Empleado

```
Aporte Pensión = Salario Base × 4%
Aporte Salud = Salario Base × 4%

Si Salario Base > $6.400.000 (4 SMMLV):
    Fondo Solidaridad = (Salario Base - $6.400.000) × 1%
Sino:
    Fondo Solidaridad = $0

Total Descuentos = Aporte Pensión + Aporte Salud + Fondo Solidaridad + Retenciones + Otros
```

#### 3. Nómina Neta (Salario del Empleado)

```
Nómina Neta = Total Ingresos - Total Descuentos
```

#### 4. Aportes Patronales (Costo Real para Empleador)

```
Aporte Pensión Empleador = Salario Base × 12%
Aporte Salud Empleador = Salario Base × 8.5%
SENA = Salario Base × 2%
ICBF = Salario Base × 3%
Caja Compensación = Salario Base × 4%
ARL = Salario Base × Tasa_ARL (según tipo empleado)

Total Aportes Patronales = Suma de todos los anteriores
```

#### 5. Costo Total (para Presupuesto)

```
Costo Total Empleado = Salario Base + Total Aportes Patronales
```

### Ejemplo Práctico

**Datos del empleado: Portero, Salario $1.600.000**

```
INGRESOS:
  Salario Base.................. $ 1.600.000
  Auxilio Transporte........... $   162.000
  ─────────────────────────────
  Total Ingresos............... $ 1.762.000

DEDUCCIONES (Empleado):
  Aporte Pensión (4%)........... $    64.000
  Aporte Salud (4%)............. $    64.000
  Fondo Solidaridad (1%)........ $        0  (salario < 4 SMMLV)
  ─────────────────────────────
  Total Deducciones............ $   128.000

NÓMINA NETA (Lo que recibe) .. $ 1.634.000

APORTES PATRONALES:
  Pensión (12%)................. $   192.000
  Salud (8.5%).................. $   136.000
  SENA (2%)..................... $    32.000
  ICBF (3%)..................... $    48.000
  Caja Compensación (4%)........ $    64.000
  ARL Portero (1%).............. $    16.000
  ─────────────────────────────
  Total Aportes Patronales..... $   488.000

COSTO TOTAL (Presupuesto):
  Salario Base + Aportes........ $ 2.088.000
```

---

## Preguntas Frecuentes

### ¿Cómo se actualiza el SMMLV?

El sistema utiliza SMMLV 2024 ($1.600.000). Si hay cambios normativos, actualizar en:

```python
# core/accounting.py
class ConstantesColombiana2024:
    SMMLV = Decimal('1600000')  # Actualizar aquí
```

### ¿Qué pasa si cometo un error en la nómina?

- Si está en estado "BORRADOR": Editar y corregir
- Si está "CONFIRMADA" o "PAGADA": Crear nota (no se puede eliminar por auditoria)

### ¿Las deducciones se calculan automáticamente?

Sí, completamente. Solo ingresa salario base, horas extras y otros ingresos.

### ¿Puedo personalizar tasas de ARL?

Sí, en el método `calcular_aporte_arl()` de `CalculadoraNomina`:

```python
def calcular_aporte_arl(self, salario, tipo_empleado):
    categorias_riesgo = {
        'PORTERO': Decimal('0.01'),  # Cambiar aquí
        # ... más tipos
    }
```

### ¿Cómo manejar empleados con contrato parcial?

Ingresar el salario proporcionalmente:
- Contrato 50%: Ingresar 50% del salario
- El sistema calcula sobre lo ingresado

### ¿Se puede descargar los reportes?

Sí, los reportes tienen opción de descarga en PDF y Excel.

### ¿Cómo configurar alertas de vencimiento?

En cada obligación fiscal:
1. Editarla
2. Cambiar campo "Días de alerta" (recomendado: 15-30 días)
3. Guardar

### ¿Es posible generar reportes retroactivos?

Sí, los reportes permiten seleccionar cualquier mes/año disponible en la BD.

---

## Información de Contacto y Soporte

- **Documentación:** Disponible en este archivo
- **Tests:** Ver `core/tests_accounting.py`
- **Código:**
  - Modelos: `core/models.py`
  - Cálculos: `core/accounting.py`
  - Vistas: `core/accounting_views.py`
  - Formularios: `core/forms.py`

---

**Última actualización:** Mayo 2024  
**Versión:** 1.0  
**Licencia:** MIT  
**Responsables:** Equipo de Desarrollo Constructora
