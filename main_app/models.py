from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language, gettext_lazy as _
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Category(models.Model):
    name_es = models.CharField(max_length=200, verbose_name=_("Nombre (ES)"))
    name_en = models.CharField(max_length=200, verbose_name=_("Nombre (EN)"), blank=True, null=True)
    name_it = models.CharField(max_length=200, verbose_name=_("Nombre (IT)"), blank=True, null=True)
    
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    
    description_es = models.TextField(verbose_name=_("Descripción (ES)"), blank=True, null=True)
    description_en = models.TextField(verbose_name=_("Descripción (EN)"), blank=True, null=True)
    description_it = models.TextField(verbose_name=_("Descripción (IT)"), blank=True, null=True)

    class Meta:
        verbose_name = _("Categoría")
        verbose_name_plural = _("Categorías")

    def __str__(self):
        return self.name_es

    @property
    def name(self):
        lang = get_language()
        if lang == 'en' and self.name_en:
            return self.name_en
        elif lang == 'it' and self.name_it:
            return self.name_it
        return self.name_es

    @property
    def description(self):
        lang = get_language()
        if lang == 'en' and self.description_en:
            return self.description_en
        elif lang == 'it' and self.description_it:
            return self.description_it
        return self.description_es


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name=_("Categoría"))
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Precio"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))
    featured = models.BooleanField(default=False, verbose_name=_("Destacado (Home)"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))

    class Meta:
        verbose_name = _("Producto")
        verbose_name_plural = _("Productos")

    def __str__(self):
        return self.name

    @property
    def name(self):
        lang = get_language()
        translation = self.translations.filter(language_code=lang).first()
        if translation and translation.name:
            return translation.name
        translation_es = self.translations.filter(language_code='es').first()
        if translation_es and translation_es.name:
            return translation_es.name
        first_trans = self.translations.first()
        if first_trans and first_trans.name:
            return first_trans.name
        return self.slug

    @property
    def description(self):
        lang = get_language()
        translation = self.translations.filter(language_code=lang).first()
        if translation and translation.description:
            return translation.description
        translation_es = self.translations.filter(language_code='es').first()
        if translation_es and translation_es.description:
            return translation_es.description
        first_trans = self.translations.first()
        if first_trans and first_trans.description:
            return first_trans.description
        return ""

    @property
    def bullet_points(self):
        lang = get_language()
        translation = self.translations.filter(language_code=lang).first()
        raw_bullets = ""
        if translation and translation.bullet_points:
            raw_bullets = translation.bullet_points
        else:
            translation_es = self.translations.filter(language_code='es').first()
            if translation_es and translation_es.bullet_points:
                raw_bullets = translation_es.bullet_points
            else:
                first_trans = self.translations.first()
                if first_trans and first_trans.bullet_points:
                    raw_bullets = first_trans.bullet_points
        
        if not raw_bullets:
            return []
        return [b.strip() for b in raw_bullets.split('\n') if b.strip()]

    @property
    def total_stock(self):
        return sum(variant.stock for variant in self.variants.filter(is_active=True))

    @property
    def has_stock(self):
        return self.total_stock > 0

    @property
    def main_image(self):
        first_img = self.images.first()
        if first_img:
            return first_img.image
        return "img/xeax_XX_plata_01.png"

    @property
    def main_image_url(self):
        first_img = self.images.first()
        if first_img:
            return first_img.image_url
        from django.templatetags.static import static
        return static("img/xeax_XX_plata_01.png")


class ProductTranslation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='translations', verbose_name=_("Producto"))
    language_code = models.CharField(max_length=10, verbose_name=_("Código de Idioma"))
    name = models.CharField(max_length=200, verbose_name=_("Nombre"))
    description = models.TextField(verbose_name=_("Descripción"))
    bullet_points = models.TextField(blank=True, null=True, help_text=_("Una característica por línea"), verbose_name=_("Bullet Points"))

    class Meta:
        verbose_name = _("Traducción de Producto")
        verbose_name_plural = _("Traducciones de Producto")
        unique_together = ('product', 'language_code')

    def __str__(self):
        return f"{self.product.slug} - {self.language_code}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_("Producto"))
    image = models.ImageField(upload_to='products/', max_length=500, verbose_name=_("Imagen"))
    order = models.IntegerField(default=0, verbose_name=_("Orden"))
    alt_text = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Texto Alternativo"))

    class Meta:
        verbose_name = _("Imagen de Producto")
        verbose_name_plural = _("Imágenes de Producto")
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.slug} - {self.image.name if self.image else ''}"

    @property
    def image_url(self):
        if not self.image:
            return ""
        # If it starts with img/, it's a static file path from old migration
        if str(self.image).startswith('img/'):
            from django.templatetags.static import static
            return static(str(self.image))
        try:
            return self.image.url
        except ValueError:
            return ""


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_("Producto"))
    size = models.CharField(max_length=50, verbose_name=_("Talla / Talle"))
    stock = models.IntegerField(default=0, verbose_name=_("Stock"))
    amazon_sku = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Amazon SKU"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Variante de Producto")
        verbose_name_plural = _("Variantes de Producto")
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size} (Stock: {self.stock})"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Carrito de {self.user.username}"
        return f"Carrito Anónimo {self.session_key}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.variant.product.name} ({self.variant.size})"

    @property
    def total_price(self):
        return self.variant.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', _('Pendiente')),
        ('Paid', _('Pagado')),
        ('Shipped', _('Enviado')),
        ('Cancelled', _('Cancelado')),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    full_name = models.CharField(max_length=200, verbose_name=_("Nombre Completo"))
    email = models.EmailField(verbose_name=_("Correo Electrónico"))
    phone = models.CharField(max_length=50, verbose_name=_("Teléfono"))
    address = models.CharField(max_length=300, verbose_name=_("Dirección"))
    city = models.CharField(max_length=100, verbose_name=_("Ciudad"))
    postal_code = models.CharField(max_length=20, verbose_name=_("Código Postal"))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name=_("Estado"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha"))

    class Meta:
        verbose_name = _("Pedido")
        verbose_name_plural = _("Pedidos")

    def __str__(self):
        return f"Pedido #{self.id} - {self.full_name}"


@receiver(pre_save, sender=Order)
def capture_previous_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Order.objects.only('status').get(pk=instance.pk).status
        except Order.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def notify_order_status_change(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, '_previous_status', None)
    if previous and previous != instance.status:
        from .emails import send_order_status_update
        send_order_status_update(instance)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Nombre del Producto"))
    size = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Talla / Talle"))
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        name = self.product_name or (self.variant.product.name if self.variant else _("Producto Eliminado"))
        size_str = f" ({self.size})" if self.size else ""
        return f"{self.quantity} x {name}{size_str}"

    @property
    def total_price(self):
        return self.price * self.quantity


class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    path = models.CharField(max_length=500)
    product_viewed = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = _("Log de Actividad")
        verbose_name_plural = _("Logs de Actividad")
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else f"Anónimo ({self.session_key[:8] if self.session_key else ''})"
        return f"{user_str} visitó {self.path} el {self.timestamp}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Teléfono"))
    shipping_address = models.CharField(max_length=300, blank=True, null=True, verbose_name=_("Dirección de Envío"))
    shipping_city = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ciudad de Envío"))
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Código Postal de Envío"))
    shipping_country = models.CharField(max_length=100, blank=True, null=True, default="España", verbose_name=_("País de Envío"))
    
    billing_name = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Nombre de Facturación"))
    billing_tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("NIF/CIF / DNI"))
    billing_address = models.CharField(max_length=300, blank=True, null=True, verbose_name=_("Dirección de Facturación"))
    billing_city = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ciudad de Facturación"))
    billing_postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Código Postal de Facturación"))
    billing_country = models.CharField(max_length=100, blank=True, null=True, default="España", verbose_name=_("País de Facturación"))
    
    birth_date = models.DateField(blank=True, null=True, verbose_name=_("Fecha de Nacimiento"))
    preferred_size = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Talla Preferida"))

    class Meta:
        verbose_name = _("Perfil de Usuario")
        verbose_name_plural = _("Perfiles de Usuario")

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=instance)
    profile.save()


class TermsAndConditions(models.Model):
    version = models.CharField(max_length=20, unique=True, verbose_name=_("Versión"))
    title_es = models.CharField(max_length=255, verbose_name=_("Título (ES)"))
    title_en = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Título (EN)"))
    title_it = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Título (IT)"))
    
    content_es = models.TextField(verbose_name=_("Contenido (ES)"))
    content_en = models.TextField(blank=True, null=True, verbose_name=_("Contenido (EN)"))
    content_it = models.TextField(blank=True, null=True, verbose_name=_("Contenido (IT)"))

    summary_es = models.TextField(blank=True, null=True, verbose_name=_("Resumen de Cambios (ES)"))
    summary_en = models.TextField(blank=True, null=True, verbose_name=_("Resumen de Cambios (EN)"))
    summary_it = models.TextField(blank=True, null=True, verbose_name=_("Resumen de Cambios (IT)"))

    is_active = models.BooleanField(default=False, verbose_name=_("Versión Activa Vigente"))
    effective_date = models.DateField(verbose_name=_("Fecha de Entrada en Vigor"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Creación"))

    class Meta:
        verbose_name = _("Términos y Condiciones")
        verbose_name_plural = _("Términos y Condiciones")
        ordering = ['-effective_date', '-id']

    def __str__(self):
        active_str = " [ACTIVA]" if self.is_active else ""
        return f"T&C {self.version}{active_str} - {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            TermsAndConditions.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    @property
    def title(self):
        lang = get_language()
        if lang == 'en' and self.title_en:
            return self.title_en
        elif lang == 'it' and self.title_it:
            return self.title_it
        return self.title_es

    @property
    def content(self):
        lang = get_language()
        if lang == 'en' and self.content_en:
            return self.content_en
        elif lang == 'it' and self.content_it:
            return self.content_it
        return self.content_es

    @property
    def summary(self):
        lang = get_language()
        if lang == 'en' and self.summary_en:
            return self.summary_en
        elif lang == 'it' and self.summary_it:
            return self.summary_it
        return self.summary_es or ""

    @classmethod
    def get_active(cls):
        active = cls.objects.filter(is_active=True).first()
        if not active:
            active = cls.objects.order_by('-effective_date', '-id').first()
        return active


class UserTermsAcceptance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='terms_acceptances', verbose_name=_("Usuario"))
    terms = models.ForeignKey(TermsAndConditions, on_delete=models.CASCADE, related_name='acceptances', verbose_name=_("Términos y Condiciones"))
    accepted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Aceptación"))
    ip_address = models.CharField(max_length=45, blank=True, null=True, verbose_name=_("Dirección IP"))
    user_agent = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("User Agent"))

    class Meta:
        verbose_name = _("Aceptación de Términos")
        verbose_name_plural = _("Aceptaciones de Términos")
        ordering = ['-accepted_at']
        unique_together = ('user', 'terms')

    def __str__(self):
        return f"{self.user.username} aceptó {self.terms.version} el {self.accepted_at.strftime('%Y-%m-%d %H:%M') if self.accepted_at else ''}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de Suscripción"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))

    # RGPD: consent tracking
    consent_ip = models.CharField(max_length=45, blank=True, null=True, verbose_name=_("IP de Consentimiento"))
    consent_terms = models.ForeignKey(
        TermsAndConditions, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='newsletter_consents',
        verbose_name=_("T&C / Política aceptada")
    )

    # Optional link to registered user
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='newsletter_subscription',
        verbose_name=_("Usuario Asociado")
    )

    class Meta:
        verbose_name = _("Suscriptor Newsletter")
        verbose_name_plural = _("Suscriptores Newsletter")
        ordering = ['-subscribed_at']

    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.email}"
