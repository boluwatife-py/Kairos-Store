from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-800/50 border border-gray-700 text-white px-4 py-3 rounded-md focus:outline-none focus:ring-0 focus:border-transparent',
            'placeholder': 'Email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-gray-800/50 border border-gray-700 text-white px-4 py-3 rounded-md focus:outline-none focus:ring-0 focus:border-transparent',
            'placeholder': 'Password'
        })
    ) 