import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario, Propiedad, PropiedadImagen, SolicitudSoporte


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

	def setUp(self):
		self.admin_user = User.objects.create_user(
			username='admin-principal',
			password='ClaveSegura123!',
			is_staff=True,
			is_superuser=True,
		)
		PerfilUsuario.objects.create(user=self.admin_user, rol=PerfilUsuario.ROL_ADMIN)
		self.client.login(username='admin-principal', password='ClaveSegura123!')

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


class AuthenticationAndSupportTests(TestCase):
	def setUp(self):
		self.propiedad_a = Propiedad.objects.create(
			nombre='Casa Bosque',
			direccion='Calle Robles 45',
			precio_mensual='980.00',
			estado='ALQUILADA',
		)
		self.propiedad_b = Propiedad.objects.create(
			nombre='Torre Central',
			direccion='Av. Siempre Viva 123',
			precio_mensual='1500.00',
			estado='ALQUILADA',
		)
		self.admin_user = User.objects.create_user(
			username='admin',
			password='ClaveSegura123!',
			is_staff=True,
			is_superuser=True,
		)
		PerfilUsuario.objects.create(user=self.admin_user, rol=PerfilUsuario.ROL_ADMIN)
		self.tenant_user = User.objects.create_user(
			username='casa-bosque-01',
			password='ClaveSegura123!',
			first_name='Laura',
			last_name='Mendez',
		)
		PerfilUsuario.objects.create(
			user=self.tenant_user,
			rol=PerfilUsuario.ROL_INQUILINO,
			propiedad=self.propiedad_a,
		)

	def test_login_redirects_to_setup_when_no_users_exist(self):
		User.objects.all().delete()

		response = self.client.get(reverse('login'))

		self.assertRedirects(response, reverse('setup'))

	def test_tenant_only_sees_assigned_property(self):
		self.client.login(username='casa-bosque-01', password='ClaveSegura123!')

		response = self.client.get(reverse('propiedades'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Casa Bosque')
		self.assertNotContains(response, 'Torre Central')

	def test_quick_support_issue_creates_ticket_for_assigned_property(self):
		self.client.login(username='casa-bosque-01', password='ClaveSegura123!')

		response = self.client.post(
			reverse('soporte_crear_rapido'),
			{
				'propiedad_id': self.propiedad_a.id,
				'categoria': SolicitudSoporte.CATEGORIA_FUGA,
			},
		)

		self.assertRedirects(response, reverse('soporte'))
		self.assertEqual(SolicitudSoporte.objects.count(), 1)
		incidencia = SolicitudSoporte.objects.get()
		self.assertEqual(incidencia.propiedad, self.propiedad_a)
		self.assertEqual(incidencia.reportado_por, self.tenant_user)

	def test_admin_can_create_house_user_from_management_view(self):
		self.client.login(username='admin', password='ClaveSegura123!')

		response = self.client.post(
			reverse('usuarios'),
			{
				'nombre_completo': 'Pedro Gomez',
				'username': 'torre-central-01',
				'email': '',
				'rol': PerfilUsuario.ROL_INQUILINO,
				'propiedad': self.propiedad_b.id,
				'telefono': '',
				'password1': 'ClaveSegura123!',
				'password2': 'ClaveSegura123!',
			},
		)

		self.assertRedirects(response, reverse('usuarios'))
		self.assertTrue(User.objects.filter(username='torre-central-01').exists())
		perfil = PerfilUsuario.objects.get(user__username='torre-central-01')
		self.assertEqual(perfil.propiedad, self.propiedad_b)
