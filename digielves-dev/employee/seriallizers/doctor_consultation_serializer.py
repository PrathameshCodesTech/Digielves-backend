
from digielves_setup.models import ConsultationReport, DoctorConsultation, DoctorConsultationDetails, DoctorSlot, User
from rest_framework import serializers



class DoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultation
        fields = [ "doctor_id","employee_id", "appointment_date","doctor_slot","organization_id",'reason_for_consultation', "meeting_pref_type"]
      
class DoctorConsultationDetailsInOneSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultationDetails
        fields = [ "full_name","relationship", "blood_group","marital_status","age",'gender', "phone_no", "employee_id"]
      
class UpdateDoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        

        fields = [ 'doctor_id',  'confirmed', 'transcript', 'next_appointment', 'appointment_date',  'reschedule_appointment', 'reason_for_reschedule', 'status','prescription_url', 'meeting_pref_type', 'dignosis' , 'advice']







class ConsultationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationReport
        fields = ['report_type', 'reports']

class DoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ['id','doctor','slots']
class ConsultationForSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultationDetails
        fields = ['id','employee_id','full_name']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','firstname','lastname','phone_no']
        
class ShowDoctorConsultationSerializer(serializers.ModelSerializer):
    doctor_id=UserSerializer()
    employee_id=UserSerializer()
    consultation_for=ConsultationForSerializer()
    doctor_slot=DoctorSlotSerializer()
    consultation_reports = ConsultationReportSerializer(many=True)
    
    class Meta:
        model=DoctorConsultation
        fields = [ 'id','appointment_date',  'reason_for_consultation','status', 'prescription_url', 'confirmed', 'meeting_url','summery_got', 'summery_generating','cancellation_reason','reschedule_time','reschedule_date','doctor_slot','consultation_for', 'employee_id', 'doctor_id', 'consultation_reports']
        # fields = '__all__'
        # depth = 2
        
        
class RescheduleConsultaionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        fields = [ 'reschedule_by', 'status', 'confirmed', 'reason_for_reschedule', 'reschedule_appointment', 'appointment_date' , ]
    


class DoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultationDetails
        fields = '__all__'



class ShowDoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultationDetails
        fields = '__all__'
        depth  = 1
        

        # fields = [ "employee_id", "gender", "full_name", "relationship", "marital_status" , "age", "gender", "mobile_no"]
     
     

class UpdateDoctorConsultationDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultation
        fields = [ 'doctor_id',  'confirmed', 'transcript', 'next_appointment', 'appointment_date','prescription_url', 'reschedule_appointment', 'reason_for_reschedule', 'status','prescription_url', 'meeting_pref_type', 'dignosis' , 'advice']


class DoctorConsultationDetailsForFilterSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    count = serializers.IntegerField()

    class Meta:
        fields = ['full_name', 'count']
        # fields = [ 'id','employee_id','full_name']



class ConsultationReportFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationReport
        fields = ['report_type']
        
class DoctorConsultationFilterSerializer(serializers.ModelSerializer):
    consultation_reports = ConsultationReportFilterSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorConsultation
        fields = ['consultation_reports']

    def get_consultation_reports(self, instance):
        reports = instance.consultation_reports.filter(reports__isnull=False).exclude(reports='')
        return ConsultationReportFilterSerializer(reports, many=True).data









class DoctorSlotInDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ['id','doctor','slots']
class ConsultationForInDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultationDetails
        fields = ['id','employee_id','full_name','gender','age','phone_no']

class UserInDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email','firstname','lastname','phone_no']
        
class ShowDoctorConsultationInDoctorSerializer(serializers.ModelSerializer):
    doctor_id=UserInDoctorSerializer()
    employee_id=UserSerializer()
    consultation_for=ConsultationForInDoctorSerializer()
    doctor_slot=DoctorSlotInDoctorSerializer()
    consultation_reports = ConsultationReportSerializer(many=True)
    
    class Meta:
        model=DoctorConsultation
        fields = [ 'id','appointment_date', 'prescription_url', 'reason_for_consultation','status',  'confirmed', 'meeting_url','summery_got', 'summery_generating','cancellation_reason','reschedule_time','reschedule_date','doctor_slot','consultation_for', 'employee_id', 'doctor_id', 'consultation_reports']











class DoctorSlotInDoctor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ['id','doctor','slots','meeting_mode']
class ConsultationForInDoctor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorConsultationDetails
        fields = ['id','employee_id','full_name','gender','relationship','blood_group','marital_status','age','phone_no']

class UserInDoctor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email','firstname','lastname','phone_no']

class ConsultationReportForDoctor_Serializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationReport
        fields = ['report_type', 'reports']
        
class ShowDoctorConsultation_Serializer(serializers.ModelSerializer):
    doctor_id=UserInDoctor_Serializer()
    employee_id=UserInDoctor_Serializer()
    consultation_for=ConsultationForInDoctor_Serializer()
    doctor_slot=DoctorSlotInDoctor_Serializer()
    consultation_reports = ConsultationReportForDoctor_Serializer(many=True)
    
    class Meta:
        model=DoctorConsultation
        fields = [ 'id','appointment_date',  'reason_for_consultation','meeting_pref_type','status', 'summery_got','summery','meeting_summery','meeting_audio','precaution','summery_generating','transcript', 'confirmed', 'meeting_url', 'cancellation_reason','reschedule_time','reschedule_date','doctor_slot','consultation_for', 'employee_id', 'doctor_id', 'consultation_reports']