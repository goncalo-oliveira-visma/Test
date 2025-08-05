from typing import Dict, Any

from drf_spectacular import openapi, serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .permissions import IsFHIRAPIUser
from .serializer import PatientSerializer
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Patient
from .serializer import PatientSerializer, PatientCreateSerializer, PatientBundleSerializer
from .validators import FHIRValidator


def create_operation_outcome(severity: str, code: str, details: str) -> Dict[str, Any]:
    """Create FHIR OperationOutcome for error responses"""
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": severity,
                "code": code,
                "diagnostics": details
            }
        ]
    }


# Swagger documentation schemas
patient_example = {
    "resourceType": "Patient",
    "active": True,
    "name": [
        {
            "use": "official",
            "family": "Doe",
            "given": ["John", "Michael"],
            "prefix": ["Mr."]
        }
    ],
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
    "address": [
        {
            "use": "home",
            "line": ["123 Main St", "Apt 4B"],
            "city": "New York",
            "state": "NY",
            "postalCode": "10001",
            "country": "USA"
        }
    ],
    "identifier": [
        {
            "use": "official",
            "system": "http://hospital.example.org/patients",
            "value": "12345"
        }
    ]
}

bundle_example = {
    "resourceType": "Bundle",
    "id": "patient-search-results",
    "type": "searchset",
    "total": 1,
    "entry": [
        {
            "resource": patient_example
        }
    ]
}

@extend_schema(
    tags=['Patient'],
    summary="Create Patient",
    description="Create a new FHIR Patient resource",
    request=PatientCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=PatientSerializer,
            description="Patient created successfully",
            examples=[OpenApiExample('Example Patient', value=patient_example)]
        ),
        400: OpenApiResponse(
            description="Bad Request - Invalid patient data",
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={"error": "Validation failed", "details": "Missing required field: name"}
                )
            ]
        )
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsFHIRAPIUser])
def create_patient(request):
    """Create a new patient record"""
    try:
        # Validate FHIR compliance
        fhir_patient = FHIRValidator.validate_patient(request.data)

        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            create_operation_outcome("error", "invalid", str(serializer.errors)),
            status=status.HTTP_400_BAD_REQUEST
        )
    except serializers.ValidationError as e:
        return Response(
            create_operation_outcome("error", "invalid", str(e)),
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=['Patient'],
    summary="List Patients",
    description="Retrieve a list of all patients in a FHIR Bundle",
    responses={
        200: OpenApiResponse(
            response=PatientBundleSerializer,
            description="List of patients retrieved successfully",
            examples=[OpenApiExample('Bundle Example', value=bundle_example)]
        )
    }
)
@api_view(['GET'])
def list_patients(request):
    """
    GET /fhir/Patient
    Retrieve a list of all patients
    """
    patients = Patient.objects.all()

    # Build FHIR Bundle response
    bundle_data = {
        "resourceType": "Bundle",
        "id": "patient-search-results",
        "type": "searchset",
        "total": patients.count(),
        "entry": []
    }

    for patient in patients:
        serializer = PatientSerializer(patient)
        bundle_data["entry"].append({
            "resource": serializer.data
        })

    return Response(bundle_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Patient'],
    summary="Get Patient",
    description="Retrieve details of a specific patient by ID",
    parameters=[
        OpenApiParameter(
            name='patient_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='The UUID of the patient to retrieve'
        )
    ],
    responses={
        200: OpenApiResponse(
            response=PatientSerializer,
            description="Patient retrieved successfully",
            examples=[OpenApiExample('Patient Example', value=patient_example)]
        ),
        400: OpenApiResponse(
            description="Invalid patient ID format",
            examples=[
                OpenApiExample(
                    'Invalid ID Error',
                    value={"error": "Invalid patient ID format"}
                )
            ]
        ),
        404: OpenApiResponse(description="Patient not found")
    }
)
@api_view(['GET'])
def get_patient(request, patient_id):
    """
    GET /fhir/Patient/{id}
    Retrieve details of a specific patient by ID
    """
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ValueError:
        return Response(
            {"error": "Invalid patient ID format"},
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema(
    tags=['Patient'],
    summary="Update Patient",
    description="Update the details of a specific patient",
    parameters=[
        OpenApiParameter(
            name='patient_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='The UUID of the patient to update'
        )
    ],
    request=PatientSerializer,
    responses={
        200: OpenApiResponse(
            response=PatientSerializer,
            description="Patient updated successfully",
            examples=[OpenApiExample('Updated Patient', value=patient_example)]
        ),
        400: OpenApiResponse(
            description="Invalid request or patient ID",
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={"error": "Invalid data provided"}
                )
            ]
        ),
        404: OpenApiResponse(description="Patient not found")
    }
)
@api_view(['PUT'])
def update_patient(request, patient_id):
    """
    PUT /fhir/Patient/{id}
    Update the details of a specific patient
    """
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response(
            {"error": "Invalid patient ID format"},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=['Patient'],
    summary="Delete Patient",
    description="Delete a specific patient record",
    parameters=[
        OpenApiParameter(
            name='patient_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='The UUID of the patient to delete'
        )
    ],
    responses={
        204: OpenApiResponse(description="Patient deleted successfully"),
        400: OpenApiResponse(
            description="Invalid patient ID format",
            examples=[
                OpenApiExample(
                    'Invalid ID Error',
                    value={"error": "Invalid patient ID format"}
                )
            ]
        ),
        404: OpenApiResponse(description="Patient not found")
    }
)
@api_view(['DELETE'])
def delete_patient(request, patient_id):
    """
    DELETE /fhir/Patient/{id}
    Delete a specific patient record
    """
    try:
        patient = get_object_or_404(Patient, id=patient_id)
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ValueError:
        return Response(
            {"error": "Invalid patient ID format"},
            status=status.HTTP_400_BAD_REQUEST
        )
