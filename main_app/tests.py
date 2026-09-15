from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from main_app.models import TermsAndConditions, UserTermsAcceptance

User = get_user_model()


class TermsAndConditionsModelTestCase(TestCase):
    def setUp(self):
        self.v1 = TermsAndConditions.objects.create(
            version="v1.0",
            title_es="Términos v1",
            content_es="<p>Contenido v1</p>",
            effective_date=timezone.now().date(),
            is_active=True
        )

    def test_active_version_management(self):
        self.assertTrue(self.v1.is_active)
        self.assertEqual(TermsAndConditions.get_active(), self.v1)

        # Create new active version v1.1
        v1_1 = TermsAndConditions.objects.create(
            version="v1.1",
            title_es="Términos v1.1",
            content_es="<p>Contenido v1.1</p>",
            effective_date=timezone.now().date(),
            is_active=True
        )
        self.v1.refresh_from_db()
        self.assertFalse(self.v1.is_active)
        self.assertTrue(v1_1.is_active)
        self.assertEqual(TermsAndConditions.get_active(), v1_1)


class LegalComplianceViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.active_terms = TermsAndConditions.objects.create(
            version="v1.0",
            title_es="Términos y Condiciones Generales",
            content_es="<p>Términos vigentes de prueba</p>",
            effective_date=timezone.now().date(),
            is_active=True
        )
        self.user_password = "StrongPassword123!"
        self.user = User.objects.create_user(
            username="testathlete",
            email="atleta@test.com",
            password=self.user_password
        )

    def test_company_pages_http_status(self):
        # About page
        response = self.client.get(reverse('main_app:about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sobre XEAX")

        # Sustainability page
        response = self.client.get(reverse('main_app:sustainability'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sostenibilidad")

        # Careers GET page
        response = self.client.get(reverse('main_app:careers'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trabaja con nosotros")

        # Careers POST application
        response = self.client.post(reverse('main_app:careers'), {
            'role': 'Technical Apparel Designer',
            'full_name': 'Carlos Perez',
            'email': 'carlos@test.com',
            'motivation': 'Me apasiona la moda deportiva'
        })
        self.assertEqual(response.status_code, 302)

    def test_dynamic_terms_detail_view(self):
        # Current active version
        response = self.client.get(reverse('main_app:terms_current'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "v1.0")

        # Explicit version code
        response = self.client.get(reverse('main_app:terms_version', kwargs={'version_code': 'v1.0'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "v1.0")

    def test_register_user_with_tc_acceptance(self):
        response = self.client.post(reverse('main_app:register'), {
            'username': 'newathlete',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'accept_terms': 'on'
        })
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newathlete')
        acceptance = UserTermsAcceptance.objects.filter(user=new_user, terms=self.active_terms).first()
        self.assertIsNotNone(acceptance)

    def test_register_user_fails_without_tc(self):
        response = self.client.post(reverse('main_app:register'), {
            'username': 'noacceptanceuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='noacceptanceuser').exists())

    def test_login_user_records_tc_acceptance(self):
        response = self.client.post(reverse('main_app:login'), {
            'username': 'testathlete',
            'password': self.user_password,
            'accept_terms': 'on'
        })
        self.assertEqual(response.status_code, 302)
        acceptance = UserTermsAcceptance.objects.filter(user=self.user, terms=self.active_terms).first()
        self.assertIsNotNone(acceptance)

    def test_user_profile_shows_tc_acceptance_status(self):
        UserTermsAcceptance.objects.create(
            user=self.user,
            terms=self.active_terms,
            ip_address="127.0.0.1"
        )
        self.client.login(username='testathlete', password=self.user_password)
        response = self.client.get(reverse('main_app:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuenta Legalmente Al Día")
        self.assertContains(response, "v1.0")
