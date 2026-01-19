from rest_framework import serializers
from .models import Contact, ContactStatusChoices


class ContactStatusSerializer(serializers.ModelSerializer):
    """Serializer for contact status model."""

    class Meta:
        model = ContactStatusChoices
        fields = ['id', 'name']


class ContactSerializer(serializers.ModelSerializer):
    """Full serializer for contact create/update/detail operations."""

    status_detail = ContactStatusSerializer(source='status', read_only=True)
    status = serializers.PrimaryKeyRelatedField(
        queryset=ContactStatusChoices.objects.all(),
        write_only=True
    )
    date_added = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'phone_number',
            'email', 'city', 'status', 'status_detail', 'date_added'
        ]

    def validate_email(self, value):
        """Check email uniqueness."""
        email = value.lower().strip()
        queryset = Contact.objects.filter(email=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Kontakt z tym adresem email już istnieje.')
        return email

    def validate_phone_number(self, value):
        """Check phone uniqueness."""
        phone = value.strip()
        queryset = Contact.objects.filter(phone_number=phone)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Kontakt z tym numerem telefonu już istnieje.')
        return phone

    def validate_first_name(self, value):
        """Normalize first name to title case."""
        return value.strip().title()

    def validate_last_name(self, value):
        """Normalize last name to title case."""
        return value.strip().title()

    def validate_city(self, value):
        """Normalize city to title case."""
        return value.strip().title()

    def to_representation(self, instance):
        """Replace status field with nested status_detail."""
        data = super().to_representation(instance)
        data['status'] = data.pop('status_detail')
        return data


class ContactListSerializer(serializers.ModelSerializer):
    """Minimal serializer for contact list view (better performance)."""

    status = serializers.StringRelatedField()
    date_added = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    class Meta:
        model = Contact
        fields = ['id', 'first_name', 'last_name', 'city', 'status', 'date_added']
