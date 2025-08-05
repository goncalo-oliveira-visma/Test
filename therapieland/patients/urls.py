from . import views
from django.urls import path, include, re_path

urlpatterns = [
    path('Patient', views.create_patient, name='create_patient'),
    path('Patient', views.list_patients, name='list_patients'),
    path('Patient/<uuid:patient_id>', views.get_patient, name='get_patient'),
    path('Patient/<uuid:patient_id>/', views.update_patient, name='update_patient'),
    path('Patient/<uuid:patient_id>/delete', views.delete_patient, name='update_patient'),
]