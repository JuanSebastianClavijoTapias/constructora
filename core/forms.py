from django import forms
from .models import Propiedad, Pago


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleImageInput(
                attrs={
                    'class': 'w-full rounded-xl border border-dashed border-slate-300 bg-surface-container-low px-4 py-3 text-sm file:mr-4 file:rounded-full file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-semibold file:text-on-primary hover:file:opacity-90',
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
            'nombre': forms.TextInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'direccion': forms.TextInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'precio_mensual': forms.NumberInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'estado': forms.Select(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'imagen_url': forms.URLInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary', 'placeholder': 'https://...'}),
            'inquilino_nombre': forms.TextInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
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
            'propiedad': forms.Select(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'inquilino_nombre': forms.TextInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'monto_mensual': forms.NumberInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date', 'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'metodo_pago': forms.TextInput(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
            'estado': forms.Select(attrs={'class': 'w-full bg-surface-container-low rounded-md py-2 px-4 shadow-sm focus:ring-primary focus:border-primary'}),
        }
