from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('login/google/', views.google_login, name='google_login'),
    path('login/google/callback/', views.google_callback, name='google_callback'),
    path('login/google/mock/', views.google_mock_consent, name='google_mock_consent'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('profile/', views.profile, name='profile'),
    path('catalog/', views.catalog, name='catalog'),
    path('support/size-guide/', views.size_guide, name='size_guide'),
    path('support/shipping/', views.shipping_info, name='shipping_info'),
    path('support/returns/', views.returns_policy, name='returns_policy'),
    path('support/contact/', views.contact, name='contact'),
    path('company/about/', views.about, name='about'),
    path('company/sustainability/', views.sustainability, name='sustainability'),
    path('company/careers/', views.careers, name='careers'),
    path('terms/', views.terms_detail, name='terms_current'),
    path('terms/<str:version_code>/', views.terms_detail, name='terms_version'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='main_app/password_reset_form.html',
             email_template_name='main_app/email/password_reset_email.txt',
             html_email_template_name='main_app/email/password_reset_email.html',
             subject_template_name='main_app/email/password_reset_subject.txt',
             success_url=reverse_lazy('main_app:password_reset_done'),
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='main_app/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='main_app/password_reset_confirm.html',
             success_url=reverse_lazy('main_app:password_reset_complete'),
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='main_app/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]


