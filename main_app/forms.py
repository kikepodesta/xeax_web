from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Teléfono')}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Dirección')}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ciudad')}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Código Postal')}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('País')}),
            'billing_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nombre de Facturación / Empresa')}),
            'billing_tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('NIF / CIF / DNI')}),
            'billing_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Dirección de Facturación')}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ciudad de Facturación')}),
            'billing_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Código Postal de Facturación')}),
            'billing_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('País de Facturación')}),
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'preferred_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ej: S, M, L, XL')}),
        }
