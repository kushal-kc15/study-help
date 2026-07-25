import re
from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Room, User


class RegisterForm(forms.Form):
    name = forms.CharField(max_length=100, label='Full Name', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Alex Johnson'}))
    email = forms.EmailField(label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    password1 = forms.CharField(label='Password', min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'At least 8 characters'}))
    password2 = forms.CharField(label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}))

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def _generate_username(self, email):
        base = re.sub(r'[^a-z0-9]', '', email.split('@')[0].lower()) or 'user'
        username = base
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        return username

    def save(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        name = self.cleaned_data.get('name', '')
        username = self._generate_username(email)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=name or None,
        )
        return user


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = ['topic', 'name', 'description']


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'bio', 'avatar']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your display name'}),
            'username': forms.TextInput(attrs={'placeholder': 'your_username'}),
            'bio': forms.Textarea(attrs={'placeholder': 'Tell others about yourself...', 'rows': 3}),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if not re.match(r'^[a-z0-9_]+$', username):
            raise forms.ValidationError('Only letters, numbers and underscores allowed.')
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already in use.')
        return email
