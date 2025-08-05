from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def fhir_exception_handler(exc, context):
    """Custom exception handler for FHIR-compliant error responses"""
    response = exception_handler(exc, context)

    if response is not None:
        operation_outcome = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "processing",
                    "diagnostics": str(exc)
                }
            ]
        }
        response.data = operation_outcome

    return response