from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


def get_site_url():
    return getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')


def send_order_confirmation(order, site_url=None):
    site_url = site_url or get_site_url()
    """Send order confirmation email after a successful checkout."""
    try:
        html_body = render_to_string(
            'main_app/email/order_confirmation.html',
            {'order': order, 'site_url': site_url},
        )
        send_mail(
            subject=str(_('Confirmación de tu pedido #%(id)s — XEAX Sports')) % {'id': order.id},
            message=str(_('Gracias por tu compra en XEAX Sports. Tu pedido #%(id)s ha sido confirmado. Visita: ')) % {'id': order.id} + site_url,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[order.email],
            html_message=html_body,
            fail_silently=True,
        )
    except Exception:
        pass  # email failure must never break the checkout flow


def send_order_status_update(order, site_url=None):
    """Send notification email when an order status changes."""
    site_url = site_url or get_site_url()
    status_labels = {
        'Pending': str(_('Pendiente')),
        'Paid': str(_('Pagado')),
        'Shipped': str(_('Enviado')),
        'Cancelled': str(_('Cancelado')),
    }
    status_label = status_labels.get(order.status, order.status)
    try:
        html_body = render_to_string(
            'main_app/email/order_status_update.html',
            {
                'order': order,
                'site_url': site_url,
                'status_label': status_label,
            },
        )
        send_mail(
            subject=str(_('Actualización de tu pedido #%(id)s — XEAX Sports')) % {'id': order.id},
            message=str(_('Tu pedido #%(id)s ha cambiado de estado a: %(status)s. Visita: ')) % {'id': order.id, 'status': status_label} + site_url,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[order.email],
            html_message=html_body,
            fail_silently=True,
        )
    except Exception:
        pass  # email failure must never break order management
