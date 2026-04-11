from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Pago, PerfilUsuario, Propiedad, SolicitudSoporte


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
        fields = ['nombre', 'direccion', 'precio_mensual', 'estado', 'imagen_url', 'inquilino_nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Casa Bosque'}),
            'direccion': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Calle Principal 123'}),
            'precio_mensual': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '1500'}),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
            'imagen_url': forms.URLInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'https://...'}),
            'inquilino_nombre': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Nombre referencial del residente'}),
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
            'metodo_pago': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Transferencia, efectivo, etc.'}),
            'estado': forms.Select(attrs={'class': SELECT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        propiedad_queryset = kwargs.pop('propiedad_queryset', None)
        super().__init__(*args, **kwargs)
        if propiedad_queryset is not None:
            self.fields['propiedad'].queryset = propiedad_queryset


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


class SoportePersonalizadoForm(forms.Form):
    propiedad_id = forms.IntegerField(widget=forms.HiddenInput())
    titulo = forms.CharField(
        label='Que dano hubo',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Describe el dano principal'}),
    )
    prioridad = forms.ChoiceField(
        label='Prioridad',
        choices=SolicitudSoporte.PRIORIDADES,
        widget=forms.Select(attrs={'class': SELECT_CLASSES}),
        initial=SolicitudSoporte.PRIORIDAD_MEDIA,
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
