from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.bundle import Bundle as FHIRBundle
from rest_framework import serializers
from fhir.resources.fhirtypes import PatientType
from typing import Dict, Any

class FHIRValidator:
    @staticmethod
    def validate_patient(data: Dict[str, Any]) -> PatientType:
        try:
            fhir_data = data.copy()
            fhir_data['resourceType'] = 'Patient'

            # Convert to FHIR Patient resource and validate
            fhir_patient = FHIRPatient(**fhir_data)

            # Validate required fields
            if not fhir_patient.name:
                raise serializers.ValidationError("Patient must have at least one name")
            if not fhir_patient.gender:
                raise serializers.ValidationError("Patient must have a gender specified")
            if not fhir_patient.birthDate:
                raise serializers.ValidationError("Patient must have a birth date")

            return fhir_patient

        except ValueError as e:
            raise serializers.ValidationError(f"Invalid FHIR Patient resource: {str(e)}")

    @staticmethod
    def validate_bundle(data: Dict[str, Any]) -> FHIRBundle:
        try:
            bundle = FHIRBundle(**data)
            bundle.resource_type = "Bundle"
            return bundle
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid FHIR Bundle: {str(e)}")