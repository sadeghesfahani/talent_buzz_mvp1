from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import User, Address, PersonalDetails


class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
            "personal_details": {
                "passport_number": "A1234567"
            },
            "addresses": [
                {
                    "address_type": "home",
                    "street_address": "123 Test St",
                    "city": "Test City",
                    "state": "Test State",
                    "postal_code": "12345",
                    "country": "Test Country"
                }
            ]
        }
        self.user = User.objects.create_user(email="existinguser@example.com", password="password123")

    def test_create_user(self):
        response = self.client.post('/user/users/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # Including the user created in setUp
        self.assertEqual(User.objects.get(email="testuser@example.com").email, "testuser@example.com")
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(Address.objects.get(user__email="testuser@example.com").street_address, "123 Test St")

    def test_edit_user_details(self):
        # Create user first
        response = self.client.post('/user/users/', self.user_data, format='json')
        user_id = response.data['id']

        # Edit the user's personal details
        edit_data = {
            "personal_details": {
                "passport_number": "B7654321"
            }
        }
        response = self.client.patch(f'/user/users/{user_id}/', edit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PersonalDetails.objects.get(user__id=user_id).passport_number, "B7654321")

    def test_add_new_address(self):
        # Create user first
        response = self.client.post('/user/users/', self.user_data, format='json')
        user_id = response.data['id']

        # Add a new address while keeping the existing one
        existing_address = Address.objects.get(user__id=user_id)
        new_address_data = {
            "addresses": [
                {
                    "id": existing_address.id,
                    "address_type": "home",
                    "street_address": "123 Test St",
                    "city": "Test City",
                    "state": "Test State",
                    "postal_code": "12345",
                    "country": "Test Country"
                },
                {
                    "address_type": "work",
                    "street_address": "456 New St",
                    "city": "New City",
                    "state": "New State",
                    "postal_code": "67890",
                    "country": "New Country"
                }
            ]
        }
        response = self.client.patch(f'/user/users/{user_id}/', new_address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Address.objects.filter(user__id=user_id).count(), 2)
        self.assertEqual(Address.objects.filter(user__id=user_id, street_address="456 New St").exists(), True)

    def test_edit_existing_address(self):
        # Create user first
        response = self.client.post('/user/users/', self.user_data, format='json')
        user_id = response.data['id']
        address_id = Address.objects.get(user__id=user_id).id

        # Edit the existing address
        edit_address_data = {
            "addresses": [
                {
                    "id": address_id,
                    "street_address": "789 Changed St",
                }
            ]
        }
        response = self.client.patch(f'/user/users/{user_id}/', edit_address_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Address.objects.get(id=address_id).street_address, "789 Changed St")

    def test_delete_user(self):
        # Create user first
        response = self.client.post('/user/users/', self.user_data, format='json')
        user_id = response.data['id']

        # Delete the user
        response = self.client.delete(f'/user/users/{user_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1)  # Only the initial user should remain
        self.assertEqual(Address.objects.count(), 0)

    def test_delete_address(self):
        # Create user first
        response = self.client.post('/user/users/', self.user_data, format='json')
        user_id = response.data['id']

        # Edit the user to remove the address
        edit_data = {
            "addresses": []
        }
        response = self.client.patch(f'/user/users/{user_id}/', edit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Address.objects.count(), 0)
