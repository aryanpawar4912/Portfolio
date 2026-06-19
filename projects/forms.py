from django import forms
from .models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Full name',
                'required': True,
                'data-form-input': ''
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Email address',
                'required': True,
                'data-form-input': ''
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Subject (optional)',
                'data-form-input': ''
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Your Message',
                'required': True,
                'rows': 5,
                'data-form-input': ''
            })
        }