from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator

# Create your models here.

class ContactStatusChoices(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nazwa statusu",
        help_text="Nazwa statusu kontaktu, np. 'nowy', 'w trakcie'",
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Opis",
        help_text="Opcjonalny opis statusu"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data utworzenia"
    )

    class Meta:
        verbose_name = "Status kontaktu"
        verbose_name_plural = "Statusy kontaktów"
        ordering = ['name']  # sortowanie alfabetyczne wg nazwy

    def get_contact_count(self):
        return self.contact_set.count()


    def __str__(self):
        return self.name


class Contact(models.Model):
    # regex walidator numeru telefonu (tylko cyfry, opcjonalnie + na początku)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Numer telefonu musi być w formacie: '+999999999'. Dozwolone 9-15 cyfr."
    )

    # basic dane
    first_name = models.CharField(
        max_length=100,
        verbose_name="Imię",
        help_text="Imię kontaktu"
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Nazwisko",
        help_text="Nazwisko kontaktu"
    )

    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        verbose_name="Numer telefonu",
        help_text="Format: +48123456789"
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Adres email",
        help_text="Unikalny adres email kontaktu"
    )

    city = models.CharField(
        max_length=100,
        verbose_name="Miasto",
        help_text="Miasto zamieszkania (używane do pobierania pogody)"
    )

    # metadane
    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data dodania",
        help_text="Data i czas dodania kontaktu do systemu"
    )

    # relacje sqlowe
    status = models.ForeignKey(
        ContactStatusChoices,
        on_delete=models.PROTECT,  # jesli sa kontakty to nie mozna usunac statusu
        verbose_name="Status",
        help_text="Aktualny status kontaktu",
        related_name='contacts'  # dostep: status.contacts.all()
    )

    class Meta:
        verbose_name = "Kontakt"
        verbose_name_plural = "Kontakty"
        ordering = ['-date_added']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),  # index dla szybszego wyszukiwania (uzyteczne jakby bylo 2E+50 kontaktow)
            models.Index(fields=['-date_added']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('contacts:detail', kwargs={'pk': self.pk})

