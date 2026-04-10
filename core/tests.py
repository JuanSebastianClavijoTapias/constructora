import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Propiedad, PropiedadImagen


SMALL_GIF = (
	b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
	b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PropiedadViewsTests(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

	def test_propiedades_search_filters_results(self):
		Propiedad.objects.create(
			nombre='Torre Central',
			direccion='Av. Siempre Viva 123',
			precio_mensual='1500.00',
			estado='DISPONIBLE',
			inquilino_nombre='Laura Méndez',
		)
		Propiedad.objects.create(
			nombre='Casa Bosque',
			direccion='Calle Robles 45',
			precio_mensual='980.00',
			estado='MANTENIMIENTO',
		)

		response = self.client.get(reverse('propiedades'), {'q': 'laura'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Torre Central')
		self.assertNotContains(response, 'Casa Bosque')
		self.assertEqual(response.context['total_propiedades'], 1)

	def test_propiedad_crear_allows_multiple_uploaded_images(self):
		image_one = SimpleUploadedFile('fachada.gif', SMALL_GIF, content_type='image/gif')
		image_two = SimpleUploadedFile('sala.gif', SMALL_GIF, content_type='image/gif')

		response = self.client.post(
			reverse('propiedad_crear'),
			{
				'nombre': 'Edificio Sol',
				'direccion': 'Av. Principal 100',
				'precio_mensual': '2200.00',
				'estado': 'DISPONIBLE',
				'imagen_url': '',
				'inquilino_nombre': '',
				'imagenes': [image_one, image_two],
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Propiedad.objects.count(), 1)
		self.assertEqual(PropiedadImagen.objects.count(), 2)
