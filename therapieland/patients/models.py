from django.db import models
from django.core.validators import RegexValidator
import uuid


class Patient(models.Model):
    # FHIR Patient Resource fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Resource metadata
    resource_type = models.CharField(max_length=10, default='Patient', editable=False)

    identifier_use = models.CharField(
        max_length=20,
        choices=[
            ('usual', 'Usual'),
            ('official', 'Official'),
            ('temp', 'Temp'),
            ('secondary', 'Secondary'),
        ],
        blank=True
    )
    identifier_system = models.URLField(blank=True)
    identifier_value = models.CharField(max_length=100, blank=True)

    # Names
    name_use = models.CharField(
        max_length=20,
        choices=[
            ('usual', 'Usual'),
            ('official', 'Official'),
            ('temp', 'Temp'),
            ('nickname', 'Nickname'),
            ('anonymous', 'Anonymous'),
            ('old', 'Old'),
            ('maiden', 'Maiden'),
        ],
        default='usual'
    )
    family_name = models.CharField(max_length=100)
    given_names = models.JSONField(default=list)
    prefix = models.CharField(max_length=20, blank=True)
    suffix = models.CharField(max_length=20, blank=True)

    # Contact information - phone, email
    telecom_phone = models.CharField(max_length=20, blank=True)
    telecom_email = models.EmailField(blank=True)

    # Demographics
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('unknown', 'Unknown'),
        ]
    )
    birth_date = models.DateField()

    # Address
    address_use = models.CharField(
        max_length=20,
        choices=[
            ('home', 'Home'),
            ('work', 'Work'),
            ('temp', 'Temp'),
            ('old', 'Old'),
            ('billing', 'Billing'),
        ],
        blank=True
    )
    address_line = models.JSONField(default=list)  # Array of address lines
    address_city = models.CharField(max_length=100, blank=True)
    address_district = models.CharField(max_length=100, blank=True)
    address_state = models.CharField(max_length=100, blank=True)
    address_postal_code = models.CharField(max_length=20, blank=True)
    address_country = models.CharField(max_length=100, blank=True)

    # Status
    active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        given_names_str = ' '.join(self.given_names) if self.given_names else ''
        return f"{given_names_str} {self.family_name}".strip()
