from rest_framework import serializers
from .models import Contact, ContactStatusChoices


class ContactStatusSerializer(serializers.ModelSerializer):
    """Serializer for ContactStatusChoices model."""

    class Meta:
        model = ContactStatusChoices
        fields = ['id', 'name']


class ContactSerializer(serializers.ModelSerializer):
    """Full serializer for Contact model - used for create/update/detail."""

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
        email = value.lower().strip()
        queryset = Contact.objects.filter(email=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Kontakt z tym adresem email już istnieje.')
        return email

    def validate_phone_number(self, value):
        phone = value.strip()
        queryset = Contact.objects.filter(phone_number=phone)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Kontakt z tym numerem telefonu już istnieje.')
        return phone

    def validate_first_name(self, value):
        return value.strip().title()

    def validate_last_name(self, value):
        return value.strip().title()

    def validate_city(self, value):
        return value.strip().title()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status'] = data.pop('status_detail')
        return data


class ContactListSerializer(serializers.ModelSerializer):
    """Minimal serializer for Contact list view."""

    status = serializers.StringRelatedField()
    date_added = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    class Meta:
        model = Contact
        fields = ['id', 'first_name', 'last_name', 'city', 'status', 'date_added']
