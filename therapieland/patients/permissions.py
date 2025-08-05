from rest_framework import permissions

class IsFHIRAPIUser(permissions.BasePermission):
    """
    Custom permission to only allow users with FHIR API access.
    """
    def has_permission(self, request, view):
        return bool(request.user and
                    request.user.is_authenticated and
                    request.user.groups.filter(name='fhir_api_users').exists())