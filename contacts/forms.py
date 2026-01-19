from django import forms
from .models import Contact, ContactStatusChoices


class ContactForm(forms.ModelForm):
    """Form for creating and editing contacts."""

    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'city', 'status']

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź imię',
                'required': True,
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Wprowadź nazwisko',
                'required': True,
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+48123456789',
                'required': True,
                'pattern': r'^\+?1?\d{9,15}$',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'przyklad@email.com',
                'required': True,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Miasto zamieszkania',
                'required': True,
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
        }

        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'phone_number': 'Numer telefonu',
            'email': 'Adres e-mail',
            'city': 'Miasto',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].empty_label = "-- Wybierz status --"

    def clean_first_name(self):
        """Validate and normalize first name."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if len(first_name) < 2:
            raise forms.ValidationError('Imię musi mieć co najmniej 2 znaki.')
        return first_name.title()

    def clean_last_name(self):
        """Validate and normalize last name."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        if len(last_name) < 2:
            raise forms.ValidationError('Nazwisko musi mieć co najmniej 2 znaki.')
        return last_name.title()

    def clean_city(self):
        """Validate and normalize city name."""
        city = self.cleaned_data.get('city', '').strip()
        if len(city) < 2:
            raise forms.ValidationError('Nazwa miasta musi mieć co najmniej 2 znaki.')
        return city.title()

    def clean_email(self):
        """Check email uniqueness (excluding current instance on edit)."""
        email = self.cleaned_data.get('email', '').lower().strip()
        queryset = Contact.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Kontakt z tym adresem email już istnieje.')
        return email

    def clean_phone_number(self):
        """Check phone uniqueness (excluding current instance on edit)."""
        phone = self.cleaned_data.get('phone_number', '').strip()
        queryset = Contact.objects.filter(phone_number=phone)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Kontakt z tym numerem telefonu już istnieje.')
        return phone


class ContactImportForm(forms.Form):
    """Form for importing contacts from CSV file."""

    csv_file = forms.FileField(
        label='Plik CSV',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        })
    )

    def clean_csv_file(self):
        """Validate CSV file extension and size."""
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise forms.ValidationError('Plik musi mieć rozszerzenie .csv')
            if csv_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Plik jest zbyt duży (maksymalnie 5MB)')
        return csv_file
