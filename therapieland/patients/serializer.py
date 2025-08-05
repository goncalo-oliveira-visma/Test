from rest_framework import serializers
from .models import Patient


class PatientCreateSerializer(serializers.Serializer):
    """Serializer for creating FHIR Patient resources"""

    resourceType = serializers.CharField(default="Patient", read_only=True)
    active = serializers.BooleanField(default=True, help_text="Whether this patient record is in active use")

    name = serializers.ListField(
        child=serializers.DictField(),
        help_text="A name associated with the patient",
        required=True
    )

    telecom = serializers.ListField(
        child=serializers.DictField(),
        help_text="A contact detail for the patient",
        required=False,
        allow_empty=True
    )

    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', 'unknown'],
        help_text="Administrative Gender - the gender that the patient is considered to have for administration and record keeping purposes",
        required=True
    )

    birthDate = serializers.DateField(
        help_text="The date of birth for the patient (YYYY-MM-DD format)",
        required=True
    )

    address = serializers.ListField(
        child=serializers.DictField(),
        help_text="Addresses for the patient",
        required=False,
        allow_empty=True
    )

    identifier = serializers.ListField(
        child=serializers.DictField(),
        help_text="An identifier for this patient",
        required=False,
        allow_empty=True
    )


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('id', 'resource_type', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """Convert to FHIR Patient Resource format"""
        data = {
            "resourceType": "Patient",
            "id": str(instance.id),
            "active": instance.active,
            "name": [
                {
                    "use": instance.name_use,
                    "family": instance.family_name,
                    "given": instance.given_names,
                }
            ],
            "telecom": [],
            "gender": instance.gender,
            "birthDate": instance.birth_date.isoformat(),
            "address": [],
            "identifier": []
        }

        # Add prefix and suffix if they exist
        if instance.prefix:
            data["name"][0]["prefix"] = [instance.prefix]
        if instance.suffix:
            data["name"][0]["suffix"] = [instance.suffix]

        # Add telecom information
        if instance.telecom_phone:
            data["telecom"].append({
                "system": "phone",
                "value": instance.telecom_phone,
                "use": "home"
            })

        if instance.telecom_email:
            data["telecom"].append({
                "system": "email",
                "value": instance.telecom_email,
                "use": "home"
            })

        # Add address information
        if any([instance.address_line, instance.address_city, instance.address_state,
                instance.address_postal_code, instance.address_country]):
            address = {}
            if instance.address_use:
                address["use"] = instance.address_use
            if instance.address_line:
                address["line"] = instance.address_line
            if instance.address_city:
                address["city"] = instance.address_city
            if instance.address_district:
                address["district"] = instance.address_district
            if instance.address_state:
                address["state"] = instance.address_state
            if instance.address_postal_code:
                address["postalCode"] = instance.address_postal_code
            if instance.address_country:
                address["country"] = instance.address_country

            data["address"].append(address)

        # Add identifier information
        if instance.identifier_value:
            identifier = {
                "value": instance.identifier_value
            }
            if instance.identifier_use:
                identifier["use"] = instance.identifier_use
            if instance.identifier_system:
                identifier["system"] = instance.identifier_system

            data["identifier"].append(identifier)

        return data

    def to_internal_value(self, data):
        """Convert from FHIR Patient Resource format to internal format"""
        internal_data = {}

        # Handle active status
        if 'active' in data:
            internal_data['active'] = data['active']

        # Handle name
        if 'name' in data and len(data['name']) > 0:
            name = data['name'][0]
            internal_data['name_use'] = name.get('use', 'usual')
            internal_data['family_name'] = name.get('family', '')
            internal_data['given_names'] = name.get('given', [])
            if 'prefix' in name and len(name['prefix']) > 0:
                internal_data['prefix'] = name['prefix'][0]
            if 'suffix' in name and len(name['suffix']) > 0:
                internal_data['suffix'] = name['suffix'][0]

        # Handle telecom
        if 'telecom' in data:
            for telecom in data['telecom']:
                if telecom.get('system') == 'phone':
                    internal_data['telecom_phone'] = telecom.get('value', '')
                elif telecom.get('system') == 'email':
                    internal_data['telecom_email'] = telecom.get('value', '')

        # Handle gender and birthDate
        if 'gender' in data:
            internal_data['gender'] = data['gender']
        if 'birthDate' in data:
            internal_data['birth_date'] = data['birthDate']

        # Handle address
        if 'address' in data and len(data['address']) > 0:
            address = data['address'][0]
            internal_data['address_use'] = address.get('use', '')
            internal_data['address_line'] = address.get('line', [])
            internal_data['address_city'] = address.get('city', '')
            internal_data['address_district'] = address.get('district', '')
            internal_data['address_state'] = address.get('state', '')
            internal_data['address_postal_code'] = address.get('postalCode', '')
            internal_data['address_country'] = address.get('country', '')

        # Handle identifier
        if 'identifier' in data and len(data['identifier']) > 0:
            identifier = data['identifier'][0]
            internal_data['identifier_use'] = identifier.get('use', '')
            internal_data['identifier_system'] = identifier.get('system', '')
            internal_data['identifier_value'] = identifier.get('value', '')

        return super().to_internal_value(internal_data)


class PatientBundleSerializer(serializers.Serializer):
    """Serializer for FHIR Bundle containing Patient resources"""

    resourceType = serializers.CharField(default="Bundle", read_only=True)
    id = serializers.CharField(default="patient-search-results", read_only=True)
    type = serializers.CharField(default="searchset", read_only=True)
    total = serializers.IntegerField(read_only=True)
    entry = serializers.ListField(child=serializers.DictField(), read_only=True)