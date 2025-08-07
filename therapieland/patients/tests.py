from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Patient
import uuid
from datetime import date
import json

from .serializer import PatientSerializer


class PatientAPITestCase(APITestCase):
    """Test case for the Patient API endpoints"""

    def setUp(self):
        # Create a user and add to fhir_api_users group
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        self.fhir_group, created = Group.objects.get_or_create(name='fhir_api_users')
        self.user.groups.add(self.fhir_group)

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.valid_patient_data = {
            "resourceType": "Patient",
            "active": True,
            "name": [{
                "use": "official",
                "family": "Doe",
                "given": ["John", "Michael"],
                "prefix": ["Mr."]
            }],
            "telecom": [
                {
                    "system": "phone",
                    "value": "+1-555-123-4567",
                    "use": "home"
                },
                {
                    "system": "email",
                    "value": "john.doe@example.com",
                    "use": "home"
                }
            ],
            "gender": "male",
            "birthDate": "1990-05-15",
            "address": [{
                "use": "home",
                "line": ["123 Main St", "Apt 4B"],
                "city": "New York",
                "state": "NY",
                "postalCode": "10001",
                "country": "USA"
            }]
        }

        self.test_patient = Patient.objects.create(
            family_name="Doe",
            given_names=["Jane"],
            gender="female",
            birth_date="1992-01-01"
        )

    def test_create_patient_valid_data(self):
        url = reverse('create_patient')
        response = self.client.post(url, self.valid_patient_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['resourceType'], 'Patient')
        self.assertEqual(response.data['name'][0]['family'], 'Doe')
        self.assertEqual(response.data['gender'], 'male')

    def test_create_patient_invalid_data(self):
        invalid_data = {
            "resourceType": "Patient",
            "gender": "invalid_gender",  # Invalid gender value
            "birthDate": "1990-05-15"
        }
        url = reverse('create_patient')
        response = self.client.post(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_patient_without_auth(self):
        self.client.credentials()

        url = reverse('create_patient')
        response = self.client.post(url, self.valid_patient_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_patient_list(self):
        url = reverse('list_patients')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['resourceType'], 'Bundle')
        self.assertEqual(response.data['type'], 'searchset')
        self.assertTrue(isinstance(response.data['entry'], list))

    def test_get_patient_detail(self):
        url = reverse('get_patient', kwargs={'patient_id': self.test_patient.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['resourceType'], 'Patient')
        self.assertEqual(response.data['name'][0]['family'], 'Doe')

    def test_get_patient_invalid_id(self):
        invalid_id = uuid.uuid4()
        url = reverse('get_patient', kwargs={'patient_id': invalid_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_patient(self):
        update_data = {
            "resourceType": "Patient",
            "name": [{
                "use": "official",
                "family": "Doe-Updated",
                "given": ["Jane", "Marie"]
            }],
            "gender": "female",
            "birthDate": "1992-01-01"
        }
        url = reverse('update_patient', kwargs={'patient_id': self.test_patient.id})
        response = self.client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'][0]['family'], 'Doe-Updated')

    def test_delete_patient(self):
        patient = Patient.objects.create(
            family_name="ToDelete",
            given_names=["Test"],
            gender="male",
            birth_date="1990-01-01"
        )

        self.assertEqual(Patient.objects.filter(id=patient.id).count(), 1)

        url = reverse('delete_patient', kwargs={'patient_id': patient.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Patient.objects.filter(id=patient.id).count(), 0)


class PatientModelTestCase(TestCase):

    def test_patient_creation(self):
        patient = Patient.objects.create(
            family_name="Smith",
            given_names=["John"],
            gender="male",
            birth_date="1990-01-01"
        )
        self.assertTrue(isinstance(patient, Patient))
        self.assertEqual(str(patient), "Will Smith")

    def test_patient_fhir_compliance(self):
        """Test FHIR compliance of patient data"""
        patient = Patient.objects.create(
            family_name="Smith",
            given_names=["Will"],
            gender="male",
            birth_date="1990-01-01",
            telecom_phone="+1-555-123-4567",
            telecom_email="john.smith@example.com",
            address_use="home",
            address_line=["123 Main St"],
            address_city="New York",
            address_state="NY",
            address_postal_code="10001",
            address_country="USA"
        )

        self.assertTrue(hasattr(patient, 'id'))
        self.assertTrue(hasattr(patient, 'resource_type'))
        self.assertEqual(patient.resource_type, 'Patient')

        self.assertTrue(isinstance(patient.id, uuid.UUID))
        self.assertTrue(isinstance(patient.birth_date, date))
        self.assertTrue(isinstance(patient.given_names, list))


class PatientSerializerTestCase(TestCase):
    def setUp(self):
        self.patient_attributes = {
            "family_name": "Smith",
            "given_names": ["Will"],
            "gender": "male",
            "birth_date": "1990-01-01",
            "telecom_phone": "+1-555-123-4567",
            "telecom_email": "john.smith@example.com"
        }
        self.patient = Patient.objects.create(**self.patient_attributes)

    def test_patient_serialization(self):
        serializer = PatientSerializer(self.patient)
        data = serializer.data

        self.assertEqual(data['resourceType'], 'Patient')
        self.assertTrue('id' in data)
        self.assertTrue('name' in data)
        self.assertTrue('gender' in data)
        self.assertTrue('birthDate' in data)

    def test_patient_deserialization(self):
        fhir_data = {
            "resourceType": "Patient",
            "name": [{
                "use": "official",
                "family": "Johnson",
                "given": ["Robert"]
            }],
            "gender": "male",
            "birthDate": "1995-05-15"
        }

        serializer = PatientSerializer(data=fhir_data)
        self.assertTrue(serializer.is_valid())
