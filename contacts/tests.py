from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Contact, ContactStatusChoices


class ContactCRUDTest(TestCase):
    """Tests for contact CRUD operations via web views."""

    def setUp(self):
        self.client = Client()
        self.status, _ = ContactStatusChoices.objects.get_or_create(
            name='nowy', defaults={'description': 'Nowy kontakt'}
        )

    def test_contact_create_and_list(self):
        """Test creating a contact and viewing it in the list."""
        response = self.client.post(reverse('contacts:create'), {
            'first_name': 'Jan',
            'last_name': 'Kowalski',
            'phone_number': '+48123456789',
            'email': 'jan@example.com',
            'city': 'Warszawa',
            'status': self.status.id
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('contacts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jan')
        self.assertContains(response, 'Kowalski')


class ContactAPITest(APITestCase):
    """Tests for contact REST API endpoints."""

    def setUp(self):
        self.status, _ = ContactStatusChoices.objects.get_or_create(
            name='nowy', defaults={'description': 'Nowy kontakt'}
        )

    def test_api_crud_operations(self):
        """Test create, read, update, delete via API."""
        # Create
        data = {
            'first_name': 'Anna',
            'last_name': 'Nowak',
            'phone_number': '+48987654321',
            'email': 'anna@example.com',
            'city': 'Kraków',
            'status': self.status.id
        }
        response = self.client.post('/api/contacts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact_id = response.data['contact']['id']

        # Read
        response = self.client.get('/api/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Update
        data['city'] = 'Gdańsk'
        response = self.client.put(f'/api/contacts/{contact_id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f'/api/contacts/{contact_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
