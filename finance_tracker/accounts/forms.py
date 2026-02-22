from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

CSS = 'form-control'
SELECT = 'form-select'


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': CSS, 'placeholder': 'you@example.com'})
    )
    first_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': CSS, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': CSS, 'placeholder': 'Last name'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': CSS, 'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': CSS, 'placeholder': 'Password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': CSS, 'placeholder': 'Confirm password'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': CSS})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': CSS}),
            'first_name': forms.TextInput(attrs={'class': CSS}),
            'last_name': forms.TextInput(attrs={'class': CSS}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'preferred_currency', 'profile_picture', 'phone_number',
            'bio', 'budget_alert_email', 'budget_alert_threshold',
        ]
        widgets = {
            'preferred_currency': forms.Select(attrs={'class': SELECT}),
            'phone_number': forms.TextInput(attrs={'class': CSS, 'placeholder': '+1 234 567 8900'}),
            'bio': forms.Textarea(attrs={'class': CSS, 'rows': 3}),
            'budget_alert_threshold': forms.NumberInput(attrs={'class': CSS, 'min': 1, 'max': 100}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
