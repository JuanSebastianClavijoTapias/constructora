from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Pago, PerfilUsuario, Propiedad, SolicitudSoporte,
    PersonalEmpleado, NominaEmpleado, EquiposUniformes,
    ObligacionFiscal, PagoObligacion,
    ContratoMantenimiento, PagoMantenimiento,
    GastoServicioPublico, ReporteContableMensual,
)


INPUT_CLASSES = (
    'w-full rounded-2xl border border-slate-200 bg-surface-container-low px-4 py-3 '
    'text-sm text-on-surface shadow-sm transition focus:border-primary focus:outline-none '
    'focus:ring-2 focus:ring-primary/10'
)

SELECT_CLASSES = (
    'w-full rounded-2xl border border-slate-200 bg-surface-container-low px-4 py-3 '
    'text-sm text-on-surface shadow-sm transition focus:border-primary focus:outline-none '
    'focus:ring-2 focus:ring-primary/10'
)

TEXTAREA_CLASSES = (
    'w-full rounded-2xl border border-slate-200 bg-surface-container-low px-4 py-3 '
    'text-sm text-on-surface shadow-sm transition focus:border-primary focus:outline-none '
    'focus:ring-2 focus:ring-primary/10'
)


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleImageInput(
                attrs={
                    'class': 'w-full rounded-2xl border border-dashed border-slate-300 bg-surface-container-low px-4 py-3 text-sm file:mr-4 file:rounded-full file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-semibold file:text-on-primary hover:file:opacity-90',
                    'accept': 'image/*',
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_image_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_image_clean(item, initial) for item in data]
        if not data:
            return []
        return [single_image_clean(data, initial)]

class PropiedadForm(forms.ModelForm):
    imagenes = MultipleImageField(
        required=False,
        label='Imágenes',
        help_text='Puedes seleccionar una o varias imágenes desde tu equipo.',
    )

    class Meta:
        model = Propiedad
        fields = ['nombre', 'direccion', 'precio_mensual', 'estado', 'imagen_url', 'inquilino_nombre', 'habitaciones', 'baños', 'patio', 'parquedero']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Casa Bosque'}),
            'direccion': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Calle Principal 123'}),
            'precio_mensual': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '1500'}),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'imagen_url': forms.URLInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'https://...'}),
            'inquilino_nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Nombre referencial del residente'}),
            'habitaciones': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '3', 'min': '0'}),
            'baños': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '2', 'min': '0'}),
            'patio': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-slate-300'}),
            'parquedero': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-slate-300'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagen_url'].label = 'Imagen por URL'
        self.fields['imagen_url'].help_text = 'Opcional. Puedes usarla si no deseas subir archivos.'
        self.order_fields([
            'nombre',
            'direccion',
            'precio_mensual',
            'estado',
            'habitaciones',
            'baños',
            'patio',
            'parquedero',
            'imagenes',
            'imagen_url',
            'inquilino_nombre',
        ])

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['propiedad', 'inquilino_nombre', 'monto_mensual', 'fecha_limite', 'metodo_pago', 'estado']
        widgets = {
            'propiedad': forms.Select(attrs={'class': SELECT_CLASSES}),
            'inquilino_nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Nombre del inquilino'}),
            'monto_mensual': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '1500'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASSES}),
            'metodo_pago': forms.Select(attrs={'class': SELECT_CLASSES}),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        propiedad_queryset = kwargs.pop('propiedad_queryset', None)
        es_inquilino = kwargs.pop('es_inquilino', False)
        super().__init__(*args, **kwargs)
        if propiedad_queryset is not None:
            self.fields['propiedad'].queryset = propiedad_queryset
        
        # Si es inquilino, ocultar y desabilitar ciertos campos
        if es_inquilino:
            # Ocultar campos que ya están asignados
            self.fields['propiedad'].widget = forms.HiddenInput()
            self.fields['inquilino_nombre'].widget = forms.HiddenInput()
            self.fields['monto_mensual'].widget = forms.HiddenInput()
            
            # Estado siempre debe ser "PAGADO" para inquilinos
            self.fields['estado'].initial = 'PAGADO'
            self.fields['estado'].widget = forms.HiddenInput()
            
            # Solo mostrar método de pago y fecha límite
            self.fields['metodo_pago'].widget = forms.Select(attrs={
                'class': SELECT_CLASSES,
            })


class PagoFormReadOnly(forms.ModelForm):
    """Versión de solo lectura para mostrar datos del pago"""
    class Meta:
        model = Pago
        fields = ['propiedad', 'inquilino_nombre', 'monto_mensual', 'fecha_limite']
        widgets = {
            'propiedad': forms.TextInput(attrs={'class': INPUT_CLASSES, 'readonly': 'readonly'}),
            'inquilino_nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'readonly': 'readonly'}),
            'monto_mensual': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'readonly': 'readonly'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASSES, 'readonly': 'readonly'}),
        }


class HouseLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario de la casa',
        widget=forms.TextInput(
            attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'casa-bosque-01',
                'autofocus': True,
            }
        ),
    )
    password = forms.CharField(
        label='Contrasena',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Ingresa tu contrasena',
            }
        ),
    )


class InitialAdminSetupForm(UserCreationForm):
    nombre_completo = forms.CharField(
        label='Nombre completo',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Administrador principal'}),
    )
    email = forms.EmailField(
        label='Correo',
        required=False,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'correo@empresa.com'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'nombre_completo', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario administrador'
        self.fields['username'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'admin-principal'})
        self.fields['password1'].label = 'Contrasena'
        self.fields['password1'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'Crea una contrasena segura'})
        self.fields['password2'].label = 'Confirmar contrasena'
        self.fields['password2'].widget.attrs.update({'class': INPUT_CLASSES, 'placeholder': 'Repite la contrasena'})

    def save(self, commit=True):
        user = super().save(commit=False)
        nombre_completo = self.cleaned_data['nombre_completo'].strip().split(maxsplit=1)
        user.first_name = nombre_completo[0]
        user.last_name = nombre_completo[1] if len(nombre_completo) > 1 else ''
        user.email = self.cleaned_data['email']
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class UsuarioCasaForm(forms.Form):
    nombre_completo = forms.CharField(
        label='Nombre del residente',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Laura Mendez'}),
    )
    username = forms.CharField(
        label='Usuario de la casa',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'torre-central-01'}),
        help_text='Este usuario sera el acceso con el que ingresa la vivienda.',
    )
    email = forms.EmailField(
        label='Correo',
        required=False,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Opcional'}),
    )
    rol = forms.ChoiceField(
        label='Tipo de acceso',
        choices=PerfilUsuario.ROLES,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
    )
    propiedad = forms.ModelChoiceField(
        label='Propiedad asociada',
        queryset=Propiedad.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
    )
    telefono = forms.CharField(
        label='Telefono',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Opcional'}),
    )
    password1 = forms.CharField(
        label='Contrasena',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Crea una contrasena segura'}),
    )
    password2 = forms.CharField(
        label='Confirmar contrasena',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Repite la contrasena'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['propiedad'].queryset = Propiedad.objects.order_by('nombre')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ya existe un usuario con ese nombre.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        rol = cleaned_data.get('rol')
        propiedad = cleaned_data.get('propiedad')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Las contrasenas no coinciden.')

        if rol == PerfilUsuario.ROL_INQUILINO and not propiedad:
            self.add_error('propiedad', 'Debes asignar una propiedad al usuario de la casa.')

        return cleaned_data

    def save(self):
        nombre_completo = self.cleaned_data['nombre_completo'].strip().split(maxsplit=1)
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=nombre_completo[0],
            last_name=nombre_completo[1] if len(nombre_completo) > 1 else '',
            is_staff=self.cleaned_data['rol'] == PerfilUsuario.ROL_ADMIN,
        )
        perfil = PerfilUsuario.objects.create(
            user=user,
            propiedad=self.cleaned_data['propiedad'],
            rol=self.cleaned_data['rol'],
            telefono=self.cleaned_data['telefono'],
        )

        if (
            perfil.rol == PerfilUsuario.ROL_INQUILINO
            and perfil.propiedad
            and not perfil.propiedad.inquilino_nombre
        ):
            perfil.propiedad.inquilino_nombre = perfil.nombre_mostrar
            perfil.propiedad.save(update_fields=['inquilino_nombre'])

        return perfil


# ========== FORMULARIOS DE CONTABILIDAD ==========

# ========== NÓMINA Y PERSONAL ==========

class PersonalEmpleadoForm(forms.ModelForm):
    """Formulario para crear/editar información de empleados."""
    
    class Meta:
        model = PersonalEmpleado
        fields = [
            'nombre_completo', 'cedula', 'tipo_empleado', 'tipo_contrato',
            'salario_mensual_base', 'fecha_inicio_contrato', 'fecha_fin_contrato',
            'correo', 'telefono', 'activo'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nombre completo del empleado'
            }),
            'cedula': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Cédula sin puntos ni guiones'
            }),
            'tipo_empleado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'tipo_contrato': forms.Select(attrs={'class': SELECT_CLASSES}),
            'salario_mensual_base': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '1600000',
                'step': '1000'
            }),
            'fecha_inicio_contrato': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'fecha_fin_contrato': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'correo': forms.EmailInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'empleado@email.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '3001234567'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-slate-300'}),
        }


class NominaEmpleadoForm(forms.ModelForm):
    """Formulario para crear/editar nómina de empleados."""
    
    class Meta:
        model = NominaEmpleado
        fields = [
            'periodo_mes', 'salario_base', 'aux_transporte', 'otros_ingresos',
            'horas_extras_100', 'horas_extras_150',
            'retenciones', 'otros_descuentos', 'estado', 'fecha_pago', 'notas'
        ]
        widgets = {
            'periodo_mes': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES,
                'help_text': 'Primer día del mes'
            }),
            'salario_base': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '1600000',
                'step': '1000'
            }),
            'aux_transporte': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '162000',
                'step': '1000'
            }),
            'otros_ingresos': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'horas_extras_100': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'horas_extras_150': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'retenciones': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'otros_descuentos': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'fecha_pago': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 3,
                'placeholder': 'Notas adicionales'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos auto-calculados (solo lectura)
        if self.instance.pk:
            self.fields['salario_base'].widget.attrs['readonly'] = 'readonly'
            # Los descuentos se mostrarán como info pero no editables


class EquiposUniformesForm(forms.ModelForm):
    """Formulario para registrar equipos y uniformes asignados."""
    
    class Meta:
        model = EquiposUniformes
        fields = [
            'categoria', 'descripcion', 'cantidad', 'costo_unitario',
            'fecha_asignacion', 'fecha_devolucion', 'notas'
        ]
        widgets = {
            'categoria': forms.Select(attrs={'class': SELECT_CLASSES}),
            'descripcion': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Descripción del equipo'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '1',
                'min': '1'
            }),
            'costo_unitario': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '50000',
                'step': '1000'
            }),
            'fecha_asignacion': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'fecha_devolucion': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 2,
                'placeholder': 'Observaciones'
            }),
        }


# ========== IMPUESTOS Y OBLIGACIONES FISCALES ==========

class ObligacionFiscalForm(forms.ModelForm):
    """Formulario para registrar obligaciones fiscales."""
    
    class Meta:
        model = ObligacionFiscal
        fields = [
            'propiedad', 'tipo_obligacion', 'descripcion', 'monto_obligacion',
            'frecuencia_pago', 'fecha_vencimiento_proximo', 'dias_alerta',
            'referencia_externa', 'activa', 'notas'
        ]
        widgets = {
            'propiedad': forms.Select(attrs={'class': SELECT_CLASSES}),
            'tipo_obligacion': forms.Select(attrs={'class': SELECT_CLASSES}),
            'descripcion': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Descripción adicional'
            }),
            'monto_obligacion': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '1000'
            }),
            'frecuencia_pago': forms.Select(attrs={'class': SELECT_CLASSES}),
            'fecha_vencimiento_proximo': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'dias_alerta': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '15',
                'min': '1'
            }),
            'referencia_externa': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Código de cuenta o referencia'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-slate-300'}),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 3,
                'placeholder': 'Notas importantes'
            }),
        }
    
    def __init__(self, *args, user=None, propiedad=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar propiedades disponibles según el usuario
        if user and hasattr(user, 'perfil'):
            profile = user.perfil
            if profile.rol == 'ADMIN':
                # Admins ven todas las propiedades
                self.fields['propiedad'].queryset = Propiedad.objects.all().order_by('nombre')
            else:
                # Otros usuarios solo ven sus propiedades asignadas
                self.fields['propiedad'].queryset = Propiedad.objects.filter(
                    usuarios__user=user
                ).distinct().order_by('nombre')
        
        # Pre-seleccionar propiedad si se proporciona
        if propiedad:
            self.fields['propiedad'].initial = propiedad
        
        # Hacer propiedad requerida
        self.fields['propiedad'].required = True


class PagoObligacionForm(forms.ModelForm):
    """Formulario para registrar pagos de obligaciones."""
    
    class Meta:
        model = PagoObligacion
        fields = [
            'monto_pagado', 'fecha_pago', 'fecha_vencimiento_original',
            'metodo_pago', 'referencia_pago', 'estado', 'notas'
        ]
        widgets = {
            'monto_pagado': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '1000'
            }),
            'fecha_pago': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'fecha_vencimiento_original': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'metodo_pago': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Transferencia, ACH, etc.'
            }),
            'referencia_pago': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Comprobante o referencia'
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 2,
                'placeholder': 'Notas adicionales'
            }),
        }


# ========== SERVICIOS DE MANTENIMIENTO ==========

class ContratoMantenimientoForm(forms.ModelForm):
    """Formulario para crear/editar contratos de mantenimiento."""
    
    class Meta:
        model = ContratoMantenimiento
        fields = [
            'propiedad', 'tipo_servicio', 'proveedor', 'costo_mensual',
            'fecha_inicio', 'fecha_fin', 'fecha_proximo_pago',
            'estado', 'telefono_proveedor', 'correo_proveedor',
            'numero_contrato', 'alerta_renovacion_dias', 'notas'
        ]
        widgets = {
            'propiedad': forms.Select(attrs={'class': SELECT_CLASSES}),
            'tipo_servicio': forms.Select(attrs={'class': SELECT_CLASSES}),
            'proveedor': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nombre del proveedor'
            }),
            'costo_mensual': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '250000',
                'step': '1000'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'fecha_proximo_pago': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'telefono_proveedor': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '3001234567'
            }),
            'correo_proveedor': forms.EmailInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'proveedor@empresa.com'
            }),
            'numero_contrato': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Número del contrato'
            }),
            'alerta_renovacion_dias': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '30',
                'min': '1'
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 3,
                'placeholder': 'Términos especiales, contactos, etc.'
            }),
        }
    
    def __init__(self, *args, user=None, propiedad=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar propiedades disponibles según el usuario
        if user and hasattr(user, 'perfil'):
            profile = user.perfil
            if profile.rol == 'ADMIN':
                # Admins ven todas las propiedades
                self.fields['propiedad'].queryset = Propiedad.objects.all().order_by('nombre')
            else:
                # Otros usuarios solo ven sus propiedades asignadas
                self.fields['propiedad'].queryset = Propiedad.objects.filter(
                    usuarios__user=user
                ).distinct().order_by('nombre')
        
        # Pre-seleccionar propiedad si se proporciona
        if propiedad:
            self.fields['propiedad'].initial = propiedad
        
        # Hacer propiedad requerida
        self.fields['propiedad'].required = True


class PagoMantenimientoForm(forms.ModelForm):
    """Formulario para registrar pagos de mantenimiento."""
    
    class Meta:
        model = PagoMantenimiento
        fields = [
            'periodo_mes', 'monto', 'estado', 'fecha_pago',
            'comprobante_pago', 'notas'
        ]
        widgets = {
            'periodo_mes': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'monto': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '1000'
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'fecha_pago': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'comprobante_pago': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Referencia de transferencia'
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 2,
                'placeholder': 'Notas'
            }),
        }


# ========== SERVICIOS PÚBLICOS ==========

class GastoServicioPublicoForm(forms.ModelForm):
    """Formulario para registrar gastos de servicios públicos."""
    
    class Meta:
        model = GastoServicioPublico
        fields = [
            'tipo_servicio', 'periodo_mes', 'cantidad_consumida', 'unidad_medida',
            'tarifa_unitaria', 'monto_total', 'es_estimacion',
            'factura_numero', 'proveedor', 'notas'
        ]
        widgets = {
            'tipo_servicio': forms.Select(attrs={'class': SELECT_CLASSES}),
            'periodo_mes': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASSES
            }),
            'cantidad_consumida': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '0.01'
            }),
            'unidad_medida': forms.Select(attrs={'class': SELECT_CLASSES}),
            'tarifa_unitaria': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '0.01'
            }),
            'monto_total': forms.NumberInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': '0',
                'step': '100'
            }),
            'es_estimacion': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded border-slate-300'}),
            'factura_numero': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Número de factura'
            }),
            'proveedor': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Empresa proveedora'
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 2,
                'placeholder': 'Observaciones'
            }),
        }


class SoportePersonalizadoForm(forms.Form):
    PRIORIDAD_CHOICES = (
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA', 'Baja'),
    )
    
    propiedad_id = forms.IntegerField(widget=forms.HiddenInput())
    titulo = forms.CharField(
        label='Que dano hubo',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Describe el dano principal'}),
    )
    prioridad = forms.ChoiceField(
        label='Prioridad',
        choices=PRIORIDAD_CHOICES,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
        initial='MEDIA',
    )
    descripcion = forms.CharField(
        label='Detalle adicional',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': TEXTAREA_CLASSES,
                'rows': 4,
                'placeholder': 'Explica que paso, desde cuando sucede y cualquier detalle util.',
            }
        ),
    )
