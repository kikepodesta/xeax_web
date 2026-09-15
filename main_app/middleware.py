from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from .models import Product, UserActivityLog

class ActivityLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # We need to make sure the session is initialized so we have a session key
        if not request.session.session_key:
            request.session.save()
            
    def process_response(self, request, response):
        # Do not log admin page actions or static files to avoid clutter
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
            
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Get User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Check if the user is viewing a product detail page
        product = None
        try:
            match = resolve(request.path)
            # Both prefix and non-prefix URLs resolve here
            if match.url_name == 'product_detail' and 'slug' in match.kwargs:
                slug = match.kwargs['slug']
                product = Product.objects.filter(slug=slug).first()
        except Exception:
            pass

        # Create log
        try:
            UserActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                path=request.path,
                product_viewed=product,
                ip_address=ip,
                user_agent=user_agent
            )
        except Exception:
            # Prevent logging errors from crashing the page
            pass

        return response
