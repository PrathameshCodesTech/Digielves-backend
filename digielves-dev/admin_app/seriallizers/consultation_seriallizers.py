
from digielves_setup.models import ConsultationReport, DoctorConsultation, DoctorConsultationDetails, OrganizationDetails, User
from rest_framework import serializers




class UserRegistraionSerializerAdmin(serializers.ModelSerializer):
    
    class Meta:
        model=User
        fields = ['email','firstname','lastname','phone_no','user_role','user_type']
        


class OrganizationSerializerAdmin(serializers.ModelSerializer):
    
    class Meta:
        model=OrganizationDetails
        fields = ['name','support_mail']



class ConsultationReportForDoctor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationReport
        fields = ['report_type', 'reports']
class ShowDoctorConsultationSerializerForAdmin(serializers.ModelSerializer):
    doctor_id=UserRegistraionSerializerAdmin(many=False)
    employee_id=UserRegistraionSerializerAdmin(many=False)
    organization_id=OrganizationSerializerAdmin(many=False)
    consultation_reports = ConsultationReportForDoctor_Serializer(many=True)
    class Meta:
        model=DoctorConsultation
        fields = [ "doctor_id","employee_id",  "organization_id", "consultation_for", "appointment_date",'reason_for_consultation', "meeting_pref_type","consultation_reports"]


