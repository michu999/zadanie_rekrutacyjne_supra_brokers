# Generated migration for seeding initial contact statuses
# This migration creates the default status options

from django.db import migrations


def create_initial_statuses(apps, schema_editor):
    """
    Create initial contact status options.
    These are the default statuses specified in the requirements.
    """
    ContactStatusChoices = apps.get_model('contacts', 'ContactStatusChoices')

    statuses = [
        {'name': 'nowy', 'description': 'Nowy kontakt dodany do systemu'},
        {'name': 'w trakcie', 'description': 'Kontakt w trakcie obsługi'},
        {'name': 'zagubiony', 'description': 'Kontakt zagubiony - brak odpowiedzi'},
        {'name': 'nieaktualny', 'description': 'Kontakt nieaktualny - dane przestarzałe'},
    ]

    for status_data in statuses:
        ContactStatusChoices.objects.get_or_create(
            name=status_data['name'],
            defaults={'description': status_data['description']}
        )


def remove_initial_statuses(apps, schema_editor):
    """
    Remove initial statuses (reverse migration).
    """
    ContactStatusChoices = apps.get_model('contacts', 'ContactStatusChoices')
    ContactStatusChoices.objects.filter(
        name__in=['nowy', 'w trakcie', 'zagubiony', 'nieaktualny']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_statuses, remove_initial_statuses),
    ]
