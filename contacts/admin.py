from django.contrib import admin
from .models import Contact, ContactStatusChoices


@admin.register(ContactStatusChoices)
class ContactStatusChoicesAdmin(admin.ModelAdmin):
    """Admin configuration for ContactStatusChoices model."""

    list_display = ['name', 'description', 'get_contact_count', 'created_at']
    search_fields = ['name', 'description']
    fields = ['name', 'description']
    readonly_fields = ['created_at']

    def get_contact_count(self, obj):
        """Display number of contacts with this status."""
        return obj.contacts.count()
    get_contact_count.short_description = 'Liczba kontaktów'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin configuration for Contact model."""

    list_display = [
        'last_name',
        'first_name',
        'phone_number',
        'email',
        'city',
        'status',
        'date_added'
    ]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number', 'city']
    list_filter = ['status', 'city', 'date_added']
    ordering = ['-date_added']
    list_display_links = ['last_name', 'first_name']
    date_hierarchy = 'date_added'
    list_per_page = 25

    fieldsets = (
        ('Dane osobowe', {
            'fields': ('first_name', 'last_name')
        }),
        ('Dane kontaktowe', {
            'fields': ('phone_number', 'email', 'city')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

    readonly_fields = ['date_added']
    actions = ['mark_as_new', 'mark_as_inactive']

    @admin.action(description='Oznacz jako nowy')
    def mark_as_new(self, request, queryset):
        """Bulk action to mark selected contacts as 'nowy'."""
        try:
            new_status = ContactStatusChoices.objects.get(name='nowy')
            updated = queryset.update(status=new_status)
            self.message_user(request, f'Zaktualizowano {updated} kontakt(ów).')
        except ContactStatusChoices.DoesNotExist:
            self.message_user(request, 'Status "nowy" nie istnieje.', level='ERROR')

    @admin.action(description='Oznacz jako nieaktualny')
    def mark_as_inactive(self, request, queryset):
        """Bulk action to mark selected contacts as 'nieaktualny'."""
        try:
            inactive_status = ContactStatusChoices.objects.get(name='nieaktualny')
            updated = queryset.update(status=inactive_status)
            self.message_user(request, f'Zaktualizowano {updated} kontakt(ów).')
        except ContactStatusChoices.DoesNotExist:
            self.message_user(request, 'Status "nieaktualny" nie istnieje.', level='ERROR')

