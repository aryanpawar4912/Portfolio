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


from django import forms
from .models import (Education, Experience, Certification, Award, 
                     Publication, Skill, CoreStrength, Interest)

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['title', 'institution', 'duration', 'description', 'order']

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title', 'company', 'duration', 'description', 'order']

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        # Reverted back to match your database columns perfectly
        fields = ['title', 'issuer', 'date', 'description', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keeps title required; makes the rest of your actual fields optional!
        self.fields['issuer'].required = False
        self.fields['date'].required = False
        self.fields['description'].required = False
        self.fields['order'].required = False

class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = ['title', 'event_organizer', 'date', 'description', 'order']

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['title', 'journal', 'publish_date', 'description', 'paper_link', 'order']

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'percentage', 'order']

class CoreStrengthForm(forms.ModelForm):
    class Meta:
        model = CoreStrength
        fields = ['name', 'icon_name', 'order']

class InterestForm(forms.ModelForm):
    class Meta:
        model = Interest
        fields = ['name', 'icon_name', 'order']