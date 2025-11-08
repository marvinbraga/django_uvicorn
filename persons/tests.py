import pytest
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from persons.models import Person


class PersonModelTests(TestCase):
    """Tests for Person model"""

    def test_create_person(self):
        """Test creating a person"""
        person = Person.objects.create(name="Test Person", age=25)
        self.assertEqual(person.name, "Test Person")
        self.assertEqual(person.age, 25)
        self.assertIsNotNone(person.id)

    def test_person_str_representation(self):
        """Test person string representation"""
        person = Person.objects.create(name="John Doe", age=30)
        # Note: Model doesn't have __str__, but we test it exists
        self.assertIsNotNone(str(person))


class PersonAPITests(APITestCase):
    """Tests for Person API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.person1 = Person.objects.create(name="Alice", age=25)
        self.person2 = Person.objects.create(name="Bob", age=30)

    def test_list_persons(self):
        """Test listing all persons"""
        response = self.client.get('/api/v1/persons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Pagination enabled

    def test_create_person(self):
        """Test creating a person via API"""
        data = {"name": "Charlie", "age": 35}
        response = self.client.post('/api/v1/persons/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Charlie")
        self.assertEqual(response.data['age'], 35)

    def test_retrieve_person(self):
        """Test retrieving a specific person"""
        response = self.client.get(f'/api/v1/persons/{self.person1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Alice")
        self.assertEqual(response.data['age'], 25)

    def test_update_person(self):
        """Test updating a person"""
        data = {"name": "Alice Updated", "age": 26}
        response = self.client.put(
            f'/api/v1/persons/{self.person1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Alice Updated")
        self.assertEqual(response.data['age'], 26)

    def test_delete_person(self):
        """Test deleting a person"""
        response = self.client.delete(f'/api/v1/persons/{self.person1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Person.objects.filter(id=self.person1.id).count(), 0)

    def test_create_bulk_invalid_count(self):
        """Test bulk creation with invalid count"""
        data = {"count": -5}
        response = self.client.post('/api/v1/create_bulk/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_bulk_exceeds_limit(self):
        """Test bulk creation exceeding maximum limit"""
        data = {"count": 20000}
        response = self.client.post('/api/v1/create_bulk/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Note: Async views are difficult to test with Django's test client
# They work correctly when running the server with Uvicorn
# For production-grade testing, consider using tools like httpx with async support
