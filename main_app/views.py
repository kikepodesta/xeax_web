from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
import urllib.parse
import requests
from .models import Category, Product, Cart, CartItem, Order, OrderItem, UserProfile, TermsAndConditions, UserTermsAcceptance, NewsletterSubscriber
from .forms import UserEditForm, UserProfileForm
from .emails import send_order_confirmation


def record_user_terms_acceptance(user, request):
    active_terms = TermsAndConditions.get_active()
    if active_terms and user and user.is_authenticated:
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        UserTermsAcceptance.objects.get_or_create(
            user=user,
            terms=active_terms,
            defaults={
                'ip_address': ip,
                'user_agent': user_agent,
            }
        )



def home(request):
    featured_products = Product.objects.filter(is_active=True, featured=True).order_by('-created_at')
    return render(request, 'main_app/home.html', {'featured_products': featured_products})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    # Find the first variant with stock > 0
    default_variant = product.variants.filter(is_active=True, stock__gt=0).first()
    # Fallback to any variant if all are out of stock
    if not default_variant:
        default_variant = product.variants.filter(is_active=True).first()
    images = list(product.images.all())
    highlights = []
    for bullet in product.bullet_points[:3]:
        title, separator, description = bullet.partition(':')
        highlights.append({
            'title': title.lstrip('0123456789. ').capitalize(),
            'description': description.strip() if separator else '',
        })
    return render(request, 'main_app/product_detail.html', {
        'product': product,
        'default_variant': default_variant,
        'product_images': images,
        'story_images': [{'image': image, 'index': index} for index, image in enumerate(images) if index],
        'highlights': highlights,
        'active_variants': product.variants.filter(is_active=True),
    })


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def merge_cart(request, user):
    session_key = request.session.session_key
    if not session_key:
        return
    session_cart = Cart.objects.filter(session_key=session_key).first()
    if session_cart:
        user_cart, created = Cart.objects.get_or_create(user=user)
        for item in session_cart.items.all():
            existing_item = user_cart.items.filter(variant=item.variant).first()
            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                item.cart = user_cart
                item.save()
        session_cart.delete()


@login_required
def view_cart(request):
    cart = get_or_create_cart(request)
    return render(request, 'main_app/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    size = request.POST.get('size')
    
    # If no size provided, find the first active variant
    if not size:
        variant = product.variants.filter(is_active=True).first()
    else:
        variant = product.variants.filter(size=size, is_active=True).first()

    if not variant:
        messages.error(request, _("La talla seleccionada no está disponible."))
        return redirect('main_app:product_detail', slug=product.slug)

    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        return redirect('main_app:view_cart')

    # Check if stock is available
    if variant.stock < quantity:
        messages.error(request, _("Lo sentimos, no hay suficiente stock disponible para esta talla."))
        return redirect('main_app:product_detail', slug=product.slug)

    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
    
    if not created:
        if cart_item.quantity + quantity > variant.stock:
            messages.error(request, _("No puedes añadir más unidades de las disponibles en stock."))
            return redirect('main_app:product_detail', slug=product.slug)
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
        
    cart_item.save()
    
    # Check if user clicked 'Comprar ya' (buy now)
    buy_now = request.POST.get('buy_now') or request.GET.get('buy_now')
    if buy_now:
        return redirect('main_app:checkout')
        
    messages.success(request, _("Producto añadido al carrito correctamente."))
    return redirect('main_app:view_cart')


@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    # Ensure this item belongs to current user's or session's cart
    cart = get_or_create_cart(request)
    if cart_item.cart != cart:
        return redirect('main_app:view_cart')

    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, _("Producto eliminado del carrito."))
    else:
        if quantity > cart_item.variant.stock:
            messages.error(request, _("No hay suficiente stock disponible para esa cantidad."))
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, _("Carrito actualizado."))
            
    return redirect('main_app:view_cart')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_or_create_cart(request)
    if cart_item.cart == cart:
        cart_item.delete()
        messages.success(request, _("Producto eliminado del carrito."))
    return redirect('main_app:view_cart')


def register_user(request):
    if request.user.is_authenticated:
        return redirect('main_app:home')
        
    active_terms = TermsAndConditions.get_active()

    if request.method == 'POST':
        terms_accepted = request.POST.get('accept_terms')
        form = UserCreationForm(request.POST)
        
        if not terms_accepted:
            messages.error(request, _("Debes aceptar los Términos y Condiciones vigentes para crear tu cuenta."))
        elif form.is_valid():
            user = form.save()
            login(request, user)
            merge_cart(request, user)
            record_user_terms_acceptance(user, request)
            messages.success(request, _("¡Registro exitoso! Bienvenido a XEAX Sports."))
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main_app:home')
    else:
        form = UserCreationForm()
        
    return render(request, 'main_app/register.html', {
        'form': form,
        'active_terms': active_terms
    })


def login_user(request):
    if request.user.is_authenticated:
        return redirect('main_app:home')
        
    active_terms = TermsAndConditions.get_active()

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        terms_accepted = request.POST.get('accept_terms')

        if not terms_accepted:
            messages.error(request, _("Debes aceptar los Términos y Condiciones vigentes para iniciar sesión."))
        elif form.is_valid():
            user = form.get_user()
            login(request, user)
            merge_cart(request, user)
            record_user_terms_acceptance(user, request)
            messages.success(request, _("¡Inicio de sesión exitoso!"))
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('main_app:home')
    else:
        form = AuthenticationForm()
        
    return render(request, 'main_app/login.html', {
        'form': form,
        'active_terms': active_terms
    })



def logout_user(request):
    logout(request)
    messages.success(request, _("Has cerrado sesión."))
    return redirect('main_app:home')


@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        messages.error(request, _("Tu carrito está vacío. No puedes proceder al checkout."))
        return redirect('main_app:view_cart')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')

        # Simple validation
        if not all([full_name, email, phone, address, city, postal_code]):
            messages.error(request, _("Por favor, completa todos los campos del formulario de envío."))
            return render(request, 'main_app/checkout.html', {'cart': cart})

        # Check stock for all items
        for item in cart.items.all():
            if item.variant.stock < item.quantity:
                messages.error(request, _(f"Lo sentimos, no hay stock suficiente de la talla {item.variant.size} del producto {item.variant.product.name}."))
                return redirect('main_app:view_cart')

        # Create Order inside a transaction
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    total_amount=cart.total_price,
                    status='Paid' # Simulating instant payment approval for checkout simplicity
                )
                
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        variant=item.variant,
                        product_name=item.variant.product.name,
                        size=item.variant.size,
                        price=item.variant.product.price,
                        quantity=item.quantity
                    )
                    # Decrement variant stock
                    item.variant.stock -= item.quantity
                    item.variant.save()
                
                # Clear cart
                cart.items.all().delete()
                
                # Update user profile with shipping details if authenticated
                if request.user.is_authenticated:
                    profile = request.user.profile
                    profile.phone = phone
                    profile.shipping_address = address
                    profile.shipping_city = city
                    profile.shipping_postal_code = postal_code
                    
                    # Update User name if not set
                    if not request.user.first_name and not request.user.last_name:
                        parts = full_name.split(' ', 1)
                        if len(parts) == 2:
                            request.user.first_name, request.user.last_name = parts
                        else:
                            request.user.first_name = full_name
                        request.user.save()
                    profile.save()
                
            site_url = request.build_absolute_uri('/').rstrip('/')
            send_order_confirmation(order, site_url)

            messages.success(request, _("¡Pedido realizado con éxito! Gracias por tu compra."))
            return redirect('main_app:order_success', order_id=order.id)
            
        except Exception as e:
            messages.error(request, _("Ocurrió un error al procesar el pedido. Inténtalo de nuevo."))
            return render(request, 'main_app/checkout.html', {'cart': cart})

    return render(request, 'main_app/checkout.html', {'cart': cart})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'main_app/order_success.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main_app/orders.html', {'orders': orders})


@login_required
def profile(request):
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _("Tu perfil ha sido actualizado correctamente."))
            return redirect('main_app:profile')
        else:
            messages.error(request, _("Por favor, corrige los errores en el formulario."))
    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        
    active_terms = TermsAndConditions.get_active()
    accepted_terms = user.terms_acceptances.select_related('terms').order_by('-accepted_at')
    latest_acceptance = accepted_terms.first()
    has_accepted_active = accepted_terms.filter(terms=active_terms).exists() if active_terms else False
        
    return render(request, 'main_app/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'active_terms': active_terms,
        'accepted_terms': accepted_terms,
        'latest_acceptance': latest_acceptance,
        'has_accepted_active': has_accepted_active,
    })





def google_login(request):
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    next_url = request.GET.get('next', '')
    if not client_id or client_id.startswith('placeholder'):
        return redirect(reverse('main_app:google_mock_consent') + f'?next={urllib.parse.quote(next_url)}')
    
    redirect_uri = request.build_absolute_uri(reverse('main_app:google_callback'))
    scope = 'openid email profile'
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': next_url
        })
    )
    return redirect(google_auth_url)


def google_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state') # holds next_url
    if not code:
        messages.error(request, _("Error al autenticar con Google."))
        return redirect('main_app:login')
        
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = request.build_absolute_uri(reverse('main_app:google_callback'))
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    try:
        res = requests.post(token_url, data=data)
        if res.status_code != 200:
            messages.error(request, _("No se pudo obtener el token de Google."))
            return redirect('main_app:login')
            
        tokens = res.json()
        access_token = tokens.get('access_token')
        
        # Fetch user info
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_res = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        if user_res.status_code != 200:
            messages.error(request, _("No se pudo obtener la información de usuario de Google."))
            return redirect('main_app:login')
            
        user_info = user_res.json()
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        if not email:
            messages.error(request, _("El correo electrónico no fue proporcionado por Google."))
            return redirect('main_app:login')
            
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email,
            'first_name': first_name,
            'last_name': last_name,
        })
        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
        login(request, user)
        merge_cart(request, user)
        record_user_terms_acceptance(user, request)
        messages.success(request, _("¡Inicio de sesión con Google exitoso!"))
        
        if state:
            return redirect(state)
        return redirect('main_app:home')
    except Exception:
        messages.error(request, _("Error de conexión durante el login con Google."))
        return redirect('main_app:login')


def google_mock_consent(request):
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        email = request.POST.get('email', 'atleta@xeax.com')
        first_name = request.POST.get('first_name', 'Atleta')
        last_name = request.POST.get('last_name', 'XEAX')
        
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email,
            'first_name': first_name,
            'last_name': last_name,
        })
        if not created:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
        login(request, user)
        merge_cart(request, user)
        record_user_terms_acceptance(user, request)
        messages.success(request, _("¡Inicio de sesión simulado con Google exitoso!"))
        
        if next_url:
            return redirect(next_url)
        return redirect('main_app:home')
        
    return render(request, 'main_app/google_mock.html', {'next': next_url})



def catalog(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from .models import ProductVariant

    # Base active products query
    products_qs = Product.objects.filter(is_active=True).distinct()

    # 1. Category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        products_qs = products_qs.filter(category__slug=category_slug)

    # 2. Max Price filter
    max_price = request.GET.get('max_price', '')
    if max_price:
        try:
            products_qs = products_qs.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # 3. Sizes filter
    sizes_str = request.GET.get('sizes', '')
    if sizes_str:
        sizes_list = [s.strip() for s in sizes_str.split(',') if s.strip()]
        if sizes_list:
            products_qs = products_qs.filter(variants__size__in=sizes_list, variants__is_active=True)

    # 4. Stock filter
    in_stock = request.GET.get('in_stock', '')
    if in_stock == '1':
        products_qs = products_qs.filter(variants__stock__gt=0, variants__is_active=True)

    # 5. Sorting
    sort = request.GET.get('sort', 'featured')
    if sort == 'price_asc':
        products_qs = products_qs.order_by('price')
    elif sort == 'price_desc':
        products_qs = products_qs.order_by('-price')
    elif sort == 'newest':
        products_qs = products_qs.order_by('-created_at')
    else:
        # Default: featured first, then newest
        products_qs = products_qs.order_by('-featured', '-created_at')

    # Total count before pagination
    total_count = products_qs.count()

    # 6. Pagination (6 products per batch)
    paginator = Paginator(products_qs, 6)
    page_num = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'main_app/catalog_grid.html', {
                'products': [],
                'page': page_num,
                'has_next': False,
                'total_count': total_count
            })
        page_obj = paginator.page(paginator.num_pages)

    # Get unique active sizes
    active_sizes = sorted(list(set(ProductVariant.objects.filter(is_active=True).values_list('size', flat=True))))

    context = {
        'products': page_obj.object_list,
        'page': page_obj.number,
        'has_next': page_obj.has_next(),
        'total_count': total_count,
        'categories': Category.objects.all(),
        'sizes': active_sizes,
        'selected_category': category_slug,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'main_app/catalog_grid.html', context)

    return render(request, 'main_app/catalog.html', context)


def size_guide(request):
    return render(request, 'main_app/size_guide.html')


def shipping_info(request):
    return render(request, 'main_app/shipping_info.html')


def returns_policy(request):
    return render(request, 'main_app/returns_policy.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        topic = request.POST.get('topic', '')
        order_number = request.POST.get('order_number', '')
        message = request.POST.get('message', '')

        messages.success(request, _('¡Gracias por contactar con XEAX Sports! Tu mensaje ha sido recibido y te responderemos en breve.'))
        return redirect('main_app:contact')

    return render(request, 'main_app/contact.html')


def about(request):
    return render(request, 'main_app/about.html')


def sustainability(request):
    return render(request, 'main_app/sustainability.html')


def careers(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        role = request.POST.get('role', '')
        messages.success(request, _('¡Gracias por tu candidatura! Hemos recibido tu solicitud para el puesto de ') + role + _('. Evaluaremos tu perfil en breve.'))
        return redirect('main_app:careers')
        
    return render(request, 'main_app/careers.html')


def terms_detail(request, version_code=None):
    all_terms = TermsAndConditions.objects.all().order_by('-effective_date', '-id')
    active_terms = TermsAndConditions.get_active()
    
    if version_code:
        selected_terms = get_object_or_404(TermsAndConditions, version=version_code)
    else:
        selected_terms = active_terms or all_terms.first()

    return render(request, 'main_app/terms.html', {
        'selected_terms': selected_terms,
        'all_terms': all_terms,
        'active_terms': active_terms,
    })


def newsletter_subscribe(request):
    """AJAX endpoint for footer newsletter subscription.

    Returns JSON:
      { "status": "ok" | "already" | "has_account" | "error", "message": "..." }
    """
    from django.http import JsonResponse
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': str(_('Método no permitido.'))}, status=405)

    email = request.POST.get('email', '').strip().lower()
    consent = request.POST.get('consent', '')

    # --- Basic validation ---
    if not email:
        return JsonResponse({'status': 'error', 'message': str(_('Por favor, introduce tu email.'))}, status=400)

    if not consent:
        return JsonResponse({'status': 'error', 'message': str(_('Debes aceptar la Política de Privacidad para suscribirte.'))}, status=400)

    # --- Already subscribed? ---
    existing = NewsletterSubscriber.objects.filter(email=email).first()
    if existing:
        if existing.is_active:
            return JsonResponse({
                'status': 'already',
                'message': str(_('¡Ya formas parte del movimiento XEAX! Revisa tu bandeja de entrada.'))
            })
        else:
            # Reactivate silently
            existing.is_active = True
            existing.save(update_fields=['is_active'])
            return JsonResponse({
                'status': 'ok',
                'message': str(_('¡Bienvenido de nuevo al movimiento XEAX!'))
            })

    # --- Email belongs to an existing user account? ---
    existing_user = User.objects.filter(email__iexact=email).first()
    has_account = existing_user is not None

    # --- Create subscriber ---
    ip = request.META.get('REMOTE_ADDR')
    active_terms = TermsAndConditions.get_active()

    subscriber = NewsletterSubscriber.objects.create(
        email=email,
        consent_ip=ip,
        consent_terms=active_terms,
        user=existing_user,
    )

    # --- Send welcome email ---
    site_url = request.build_absolute_uri('/').rstrip('/')
    try:
        html_body = render_to_string(
            'main_app/email/newsletter_welcome.html',
            {'site_url': site_url},
            request=request,
        )
        send_mail(
            subject=str(_('Bienvenido al movimiento XEAX — Where I Belong')),
            message=str(_('Bienvenido a XEAX Sports. Visita: ')) + site_url + '/catalog/',
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[email],
            html_message=html_body,
            fail_silently=True,
        )
    except Exception:
        pass  # email failure must never break the subscription flow

    # --- Build response ---
    if has_account:
        login_url = request.build_absolute_uri(reverse('main_app:login'))
        return JsonResponse({
            'status': 'has_account',
            'message': str(_('¡Suscrito! Detectamos que ya tienes una cuenta con este email.')),
            'login_url': login_url,
        })

    return JsonResponse({
        'status': 'ok',
        'message': str(_('¡Bienvenido al movimiento XEAX! Te hemos enviado un email de bienvenida.'))
    })
