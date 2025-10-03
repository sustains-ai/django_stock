# Consolidated Forms for Portfolio Management Application

from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.models import User
from .models import Stock, Portfolio, FundManager, UserProfile, Institute, InstituteRole


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['symbol', 'name', 'quantity', 'price']
        widgets = {
            'symbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., AAPL, GOOGL, MSFT'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Apple Inc., Google, Microsoft'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of shares',
                'min': '1'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price per share (optional)',
                'step': '0.01',
                'min': '0'
            })
        }


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['name', 'description']


# User Management Forms
class UserCreationForm(forms.Form):
    """Form for admins to create new users"""
    
    ROLE_CHOICES = [
        ('admin', 'Institute Admin'),
        ('manager', 'Fund Manager'),
        ('analyst', 'Analyst'),
    ]
    
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    temporary_password = forms.CharField(
        max_length=128, 
        required=True,
        widget=forms.PasswordInput,
        help_text="User will be required to change this password on first login"
    )
    
    def __init__(self, *args, **kwargs):
        self.institute = kwargs.pop('institute', None)
        super().__init__(*args, **kwargs)
        
        # Add form styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class UserInvitationForm(forms.Form):
    """Form for sending user invitations"""
    
    ROLE_CHOICES = [
        ('admin', 'Institute Admin'),
        ('manager', 'Fund Manager'),
        ('analyst', 'Analyst'),
    ]
    
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional personal message to include in the invitation"
    )
    
    def __init__(self, *args, **kwargs):
        self.institute = kwargs.pop('institute', None)
        super().__init__(*args, **kwargs)
        
        # Add form styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class PasswordChangeForm(forms.Form):
    """Form for users to change their password"""
    
    current_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )
    new_password1 = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )
    new_password2 = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput,
        required=True
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Add form styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Your current password is incorrect.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("The two password fields didn't match.")
        
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }
