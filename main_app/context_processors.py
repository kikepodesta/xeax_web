from .models import Cart, TermsAndConditions

def cart_context(request):
    cart = None
    cart_total_items = 0
    
    if request.user.is_authenticated:
        # Get cart by user
        cart = Cart.objects.filter(user=request.user).first()
    else:
        # Get cart by session
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            
    if cart:
        cart_total_items = cart.total_items

    active_terms = TermsAndConditions.get_active()
        
    return {
        'cart': cart,
        'cart_total_items': cart_total_items,
        'global_active_terms': active_terms,
    }

