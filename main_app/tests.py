from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from main_app.models import TermsAndConditions, UserTermsAcceptance, Product, ProductTranslation, ProductImage, ProductVariant

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


class ProductExperienceTestCase(TestCase):
    def setUp(self):
        Product.objects.update(featured=False)
        self.product = Product.objects.create(slug='test-grips', price='39.90', featured=True)
        ProductTranslation.objects.create(
            product=self.product, language_code='es', name='Test Grips',
            description='Descripción técnica del producto.',
            bullet_points='Agarre firme\nAjuste cómodo\nLibertad de movimiento'
        )
        self.variant = ProductVariant.objects.create(product=self.product, size='M', stock=5)
        ProductVariant.objects.create(product=self.product, size='Oculta', stock=10, is_active=False)

    def test_home_slider_precedes_existing_grid(self):
        response = self.client.get(reverse('main_app:home'))
        self.assertContains(response, 'id="featured-slider"', count=1)
        self.assertContains(response, 'xeax-split-card')
        content = response.content.decode()
        self.assertLess(content.index('hero-video-bg'), content.index('id="featured-slider"'))
        self.assertLess(content.index('id="featured-slider"'), content.index('xeax-editorial-catalog'))
        self.assertContains(response, 'data-featured-slide', count=1)
        self.assertContains(response, 'class="showcase-background"', count=1)
        self.assertContains(response, 'Ver más')
        self.assertNotContains(response, 'id="featured-title"')
        self.assertNotContains(response, 'showcase-heading')
        self.assertContains(response, reverse('main_app:product_detail', args=[self.product.slug]))

    def test_home_excludes_inactive_and_nonfeatured_products(self):
        Product.objects.create(slug='not-featured', price='10.00')
        Product.objects.create(slug='inactive-featured', price='10.00', featured=True, is_active=False)
        response = self.client.get(reverse('main_app:home'))
        self.assertNotContains(response, '/product/not-featured/')
        self.assertNotContains(response, '/product/inactive-featured/')

    def test_empty_home_has_no_slider(self):
        self.product.featured = False
        self.product.save()
        response = self.client.get(reverse('main_app:home'))
        self.assertNotContains(response, 'id="featured-slider"')
        self.assertNotContains(response, 'xeax-split-card')

    def test_product_landing_uses_content_and_complete_gallery(self):
        for index in range(9):
            ProductImage.objects.create(
                product=self.product, image=f'products/test-{index}.jpg',
                order=index, alt_text=f'Detalle {index}'
            )
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertContains(response, 'id="product-experience"')
        self.assertContains(response, 'id="product-purchase"')
        self.assertContains(response, 'Agarre firme')
        self.assertContains(response, 'Descripción técnica del producto.')
        self.assertContains(response, 'data-story-image', count=8)
        self.assertContains(response, 'products/test-8.jpg')
        self.assertNotContains(response, 'data-size="Oculta"')
        self.assertContains(response, 'Inicia sesión para comprar')

    def test_product_without_images_or_stock_still_renders(self):
        self.variant.stock = 0
        self.variant.save()
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertContains(response, 'id="product-experience"')
        self.assertContains(response, 'img/xeax_XX_plata_01.png')
        self.assertNotContains(response, 'data-story-image')
        self.assertContains(response, 'Temporalmente sin stock')

    def test_authenticated_purchase_controls_are_preserved(self):
        user = User.objects.create_user(username='buyer')
        self.client.force_login(user)
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertContains(response, 'id="add-to-cart-btn"')
        self.assertContains(response, 'name="buy_now" value="1"')
        self.assertContains(response, reverse('main_app:add_to_cart', args=[self.product.id]))

    def test_purchase_form_adds_selected_variant(self):
        self.client.force_login(User.objects.create_user(username='cart-buyer'))
        response = self.client.post(reverse('main_app:add_to_cart', args=[self.product.id]), {
            'size': self.variant.size, 'quantity': 2,
        })
        self.assertRedirects(response, reverse('main_app:view_cart'))
        item = self.variant.cart_items.get()
        self.assertEqual(item.quantity, 2)

    def test_buy_now_keeps_checkout_flow(self):
        self.client.force_login(User.objects.create_user(username='checkout-buyer'))
        response = self.client.post(reverse('main_app:add_to_cart', args=[self.product.id]), {
            'size': self.variant.size, 'quantity': 1, 'buy_now': '1',
        })
        self.assertRedirects(response, reverse('main_app:checkout'))

    def test_missing_editorial_content_omits_empty_sections(self):
        self.product.translations.update(description='', bullet_points='')
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertContains(response, 'id="product-title"')
        self.assertNotContains(response, 'id="highlights-title"')
        self.assertNotContains(response, 'id="product-story"')

    def test_variant_names_are_safe_in_javascript(self):
        self.variant.size = "L'édition </script>"
        self.variant.save()
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertContains(response, r"L\u0027édition \u003C/script\u003E")
        self.assertNotContains(response, "selectSize('L'édition")

    def test_inactive_product_is_not_public(self):
        self.product.is_active = False
        self.product.save()
        response = self.client.get(reverse('main_app:product_detail', args=[self.product.slug]))
        self.assertEqual(response.status_code, 404)
