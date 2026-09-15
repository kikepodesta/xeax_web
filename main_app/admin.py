from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, ProductTranslation, ProductImage, ProductVariant, Cart, CartItem, Order, OrderItem, UserActivityLog, UserProfile, TermsAndConditions, UserTermsAcceptance, NewsletterSubscriber

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_es', 'name_en', 'name_it', 'slug')
    prepopulated_fields = {'slug': ('name_es',)}
    search_fields = ('name_es', 'name_en', 'name_it', 'slug')


class ProductTranslationInline(admin.StackedInline):
    model = ProductTranslation
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'total_stock', 'is_active', 'featured', 'created_at')
    list_filter = ('is_active', 'featured', 'category')
    search_fields = ('slug', 'translations__name')
    inlines = [ProductTranslationInline, ProductImageInline, ProductVariantInline]
    prepopulated_fields = {}


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ('variant',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'session_key', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('variant',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'address', 'city', 'postal_code')
    inlines = [OrderItemInline]


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'session_key', 'path', 'product_viewed', 'ip_address')
    list_filter = ('timestamp', 'path', 'product_viewed')
    search_fields = ('path', 'session_key', 'ip_address', 'user__username')
    readonly_fields = ('user', 'session_key', 'path', 'product_viewed', 'ip_address', 'user_agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'shipping_city', 'shipping_country', 'preferred_size')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'shipping_address', 'shipping_city', 'billing_name', 'billing_tax_id')
    fieldsets = (
        (_('Usuario'), {
            'fields': ('user', 'birth_date', 'preferred_size')
        }),
        (_('Datos de Envío'), {
            'fields': ('phone', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country')
        }),
        (_('Datos de Facturación'), {
            'fields': ('billing_name', 'billing_tax_id', 'billing_address', 'billing_city', 'billing_postal_code', 'billing_country')
        }),
    )


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ('version', 'title_es', 'is_active', 'effective_date', 'created_at')
    list_filter = ('is_active', 'effective_date')
    search_fields = ('version', 'title_es', 'content_es')

    fieldsets = (
        (_('Información Básica'), {
            'fields': ('version', 'is_active', 'effective_date')
        }),
        (_('Español (ES)'), {
            'fields': ('title_es', 'summary_es', 'content_es')
        }),
        (_('English (EN)'), {
            'fields': ('title_en', 'summary_en', 'content_en')
        }),
        (_('Italiano (IT)'), {
            'fields': ('title_it', 'summary_it', 'content_it')
        }),
    )


@admin.register(UserTermsAcceptance)
class UserTermsAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'terms', 'accepted_at', 'ip_address')
    list_filter = ('terms', 'accepted_at')
    search_fields = ('user__username', 'user__email', 'terms__version', 'ip_address')
    readonly_fields = ('user', 'terms', 'accepted_at', 'ip_address', 'user_agent')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active', 'user', 'consent_terms', 'consent_ip')
    list_filter = ('is_active', 'subscribed_at', 'consent_terms')
    search_fields = ('email', 'user__username', 'user__email', 'consent_ip')
    readonly_fields = ('email', 'subscribed_at', 'consent_ip', 'consent_terms', 'user')
    actions = ['deactivate_selected', 'activate_selected']

    @admin.action(description=_('Desactivar suscriptores seleccionados'))
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_('Activar suscriptores seleccionados'))
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
