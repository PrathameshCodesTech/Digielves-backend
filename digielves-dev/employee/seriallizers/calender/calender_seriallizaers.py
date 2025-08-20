from digielves_setup.models import CalenderReminder, DoctorSlot, MeettingSummery, ReminderToSchedule, SubTaskChild, SubTasks, DoctorConsultation, Events, Meettings, TaskHierarchy, TaskStatus, Tasks, User
from rest_framework import serializers
from datetime import datetime, date, time


class CalenderReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalenderReminder
        fields = '__all__'
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task_topic', 'due_date']


class CombinedEventMeetingSerializer(serializers.Serializer):
    category = serializers.CharField(max_length=10)
    title = serializers.CharField()
    from_date = serializers.DateField()
    from_time = serializers.TimeField()
    to_date = serializers.DateField(allow_null=True)
    to_time = serializers.TimeField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    attachment = serializers.CharField(allow_null=True)
    task_topic = serializers.CharField(allow_null=True)
    due_date = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()
    guest_data = serializers.SerializerMethodField()
    participant_data = serializers.SerializerMethodField()
    assign_to_data = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    other_participant_email = serializers.CharField(allow_null=True)
    
    def get_created_by(self, obj):
        if hasattr(obj, 'created_by'):
            return {
                "id": obj.created_by.id,
                "email": obj.created_by.email,
                "firstname": obj.created_by.firstname,
                "lastname": obj.created_by.lastname,
            }
        elif hasattr(obj, 'user_id'):
            try:
                return {
                    "id": obj.user_id.id,
                    "email": obj.user_id.email,
                    "firstname": obj.user_id.firstname,
                    "lastname": obj.user_id.lastname,
                }
            except:
                return {
                    "id": obj.user.id,
                    "email": obj.user.email,
                    "firstname": obj.user.firstname,
                    "lastname": obj.user.lastname,
                }
                
        elif hasattr(obj, 'employee_id'):
            return {
                "id": obj.employee_id.id,
                "email": obj.employee_id.email,
                "firstname": obj.employee_id.firstname,
                "lastname": obj.employee_id.lastname,
            }
        else:
            print(f"Object has no valid 'created_by' field: {obj}")
            return {
                "id": None,
                "email": None,
                "firstname": None,
                "lastname": None,
            }
    
    def to_representation(self, instance):
        if isinstance(instance, Events):
            data = {
                'category': 'Event',
                'id': instance.id,
                'title': instance.title,
                'from_datetime' : datetime.combine(instance.from_date, instance.from_time or time(0, 0)) if instance.from_date else "",
                'to_datetime': datetime.combine(instance.to_date, instance.to_time or time(0, 0)) if instance.to_date and instance.to_time else "",
                # 'from_date': instance.from_date,
                # 'from_time': instance.from_time,
                # 'to_date': instance.to_date,
                # 'to_time': instance.to_time,
                # 'description': instance.description,
                # 'attachment': instance.attachment,
                # 'guest_ids': list(instance.guest.values_list('id', flat=True)),
                'due_date': None,
                'created_by': self.get_created_by(instance)
            }
        elif isinstance(instance, Meettings):
            data = {
                'category': 'Meeting',
                'id': instance.id,
                'title': instance.title,
                # 'from_date': instance.from_date,
                'from_datetime' : datetime.combine(instance.from_date, instance.from_time or time(0, 0)) if instance.from_date else "",
                'to_datetime': datetime.combine(instance.to_date, instance.to_time or time(0, 0)) if instance.to_date and instance.to_time else "", 
                # 'to_date': instance.to_date,
                # 'to_time': instance.to_time,
                # 'meet_link': instance.meet_link,
                # 'description': instance.purpose,
                # 'attachment': None,
                # 'participant_ids': list(instance.participant.values_list('id', flat=True)),
                # 'other_participant_email': instance.other_participant_email,
                'due_date': None,
                'created_by': self.get_created_by(instance)
            }
        elif isinstance(instance, TaskHierarchy):
            data = {
                'category': 'Task',
                'id': instance.id,
                'title': instance.task_topic,
                'from_datetime' : instance.due_date,
                'to_datetime' : instance.due_date,
      
                'due_date': instance.due_date,
                'created_by': self.get_created_by(instance)
            }
        elif isinstance(instance, DoctorConsultation):
            data = {
                'category': 'consulation',
                'id': instance.id,
                'title': f"Consultation with {instance.doctor_id.firstname} {instance.doctor_id.lastname}",
                'from_datetime': datetime.combine(
                        datetime.strptime(instance.appointment_date, '%Y-%m-%d').date() if isinstance(instance.appointment_date, str) else instance.appointment_date,
                        datetime.strptime(DoctorSlot.objects.get(id=instance.doctor_slot.id).slots.split(' - ')[0], '%H:%M').time()
                    ).isoformat(),
                'to_datetime': datetime.combine(
                        datetime.strptime(instance.appointment_date, '%Y-%m-%d').date() if isinstance(instance.appointment_date, str) else instance.appointment_date,
                        datetime.strptime(DoctorSlot.objects.get(id=instance.doctor_slot.id).slots.split(' - ')[0], '%H:%M').time()
                    ).isoformat(),
    
                
                # 'created_by': self.get_created_by(instance)
            }
        elif isinstance(instance, ReminderToSchedule):
            
            try:
                related_model = instance.content_type.model_class()  # Get the model class
                related_object = related_model.objects.get(id=instance.object_id)  # Fetch the related object
         
                # Determine the category and title based on the content type
                if instance.content_type.model == "taskhierarchy":
                    
                    category = "Task"
                    title = related_object.task_topic if hasattr(related_object, 'task_topic') else ""
                elif instance.content_type.model == "meetings":
                    category = "Meeting"
                    title = related_object.title if hasattr(related_object, 'title') else ""
                else:
                    category = ""
                    title = ""

                # Construct the data dictionary

                data = {
                    'category': category,
                    'sub_category': 'reschedule',
                    'id': instance.object_id,
                    'title': title,
                    
                    'from_datetime' : instance.scheduled_time,
                    'to_datetime' : instance.scheduled_time,

                    # 'created_by': self.get_created_by(instance)
                }
            except related_model.DoesNotExist:
                data = {
                    'category': "",
                    'sub_category': "",
                    'id': instance.object_id,
                    'title': "Related object not found",
                    'from_date': None,
                    'from_time': None,
                    'due_date': instance.scheduled_time,
                    # 'created_by': self.get_created_by(instance)
                }
                
        else:
            data = {}

        return data


# class CombinedEventMeetingSerializer(serializers.Serializer):
#     category = serializers.CharField(max_length=10)
#     title = serializers.CharField()
#     from_date = serializers.DateField()
#     from_time = serializers.TimeField()
#     to_date = serializers.DateField(allow_null=True)
#     to_time = serializers.TimeField(allow_null=True)
#     description = serializers.CharField(allow_null=True)
#     attachment = serializers.CharField(allow_null=True)
#     task_topic = serializers.CharField(allow_null=True)
#     due_date = serializers.CharField(allow_null=True)
#     id = serializers.IntegerField()
#     def to_representation(self, instance):
#         if isinstance(instance, Events):
#             data = {
#                 'category': 'Event',
#                 'id': instance.id,

                
#                 'title': instance.title,
#                 'from_date': instance.from_date,
#                 'from_time': instance.from_time,
#                 'to_date': instance.to_date,
#                 'to_time': instance.to_time,
#                 'description': instance.description,
#                 'attachment': instance.attachment,

#                 'due_date': None
#             }
#         elif isinstance(instance, Meettings):
#             data = {
#                 'category': 'Meeting',
#                 'id': instance.id,
#                 'title': instance.title,
#                 'from_date': instance.from_date,
#                 'from_time': instance.from_time,
#                 'to_date': instance.to_date,
#                 'to_time': instance.to_time,
#                 'description': instance.purpose,
#                 'attachment': None,
                
#                 'due_date': None
#             }
#         elif isinstance(instance, Tasks):
#             data = {
#                 'category': 'Task',
#                 'id': instance.id,
#                 'title': instance.task_topic,
#                 'from_date': None,
#                 'from_time': None,
#                 'to_date': None,
#                 'to_time': None, 
#                 'description': instance.task_description,
#                 'attachment': None, 
                
#                 'due_date': instance.due_date
#             }
#         else:
#             data = {}

#         return data

# class CombinedEventMeetingSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     user_id = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
#     event_type = serializers.CharField(source='category')
#     title = serializers.CharField()
#     from_date = serializers.DateField()
#     from_time = serializers.TimeField(allow_null=True)
#     to_date = serializers.DateField(allow_null=True)
#     to_time = serializers.TimeField(allow_null=True)
#     description = serializers.CharField(allow_null=True)
#     meet_link = serializers.CharField(allow_null=True)
#     purpose = serializers.CharField(allow_null=True)

#     def to_representation(self, instance):
#         if isinstance(instance, Events):
#             return {
#                 **super().to_representation(instance),
#                 'event_type': 'Event'
#             }
#         elif isinstance(instance, Meettings):
#             return {
#                 **super().to_representation(instance),
#                 'event_type': 'Meeting'
#             }


# Serializer for Events
class EventCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'

# Serializer for Meettings
class MeetingCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meettings
        exclude = ['participant']

# Serializer for Tasks
class TasksCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        exclude = ['created_by','assign_to']


class MeetingCalenderDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meettings
        fields = '__all__'

class EventCalenderDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'


class CombinedEventMeetingSerializerOnly(serializers.Serializer):
    category = serializers.CharField(max_length=10)
    title = serializers.CharField()
    from_date = serializers.DateField()
    from_time = serializers.TimeField()
    to_date = serializers.DateField(allow_null=True)
    to_time = serializers.TimeField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    attachment = serializers.CharField(allow_null=True)
    task_topic = serializers.CharField(allow_null=True)
    due_date = serializers.CharField(allow_null=True)
    id = serializers.IntegerField()
    guest_data = serializers.SerializerMethodField()
    participant_data = serializers.SerializerMethodField()
    assign_to_data = serializers.SerializerMethodField()
    
    def to_representation(self, instance):
        if isinstance(instance, Events):
            data = {
                'category': 'Event',
                'id': instance.id,
                'title': instance.title,
                'from_date': instance.from_date,
                'from_time': instance.from_time,
                'to_date': instance.to_date,
                'to_time': instance.to_time,
                'description': instance.description,
                'attachment': instance.attachment,
                'guest_ids': list(instance.guest.values_list('id', flat=True)),
                'due_date': None
            }
        elif isinstance(instance, Meettings):
            data = {
                'category': 'Meeting',
                'id': instance.id,
                'title': instance.title,
                'meet_link': instance.meet_link,
                'from_date': instance.from_date,
                'from_time': instance.from_time,
                'to_date': instance.to_date,
                'to_time': instance.to_time,
                'description': instance.purpose,
                'attachment': None,
                'participant_ids': list(instance.participant.values_list('id', flat=True)),
                'due_date': None
            }
        elif isinstance(instance, DoctorConsultation):
            data = {
                'category': 'Consultation',
                'id': instance.id,
                'title': f"Consulation with dr. {instance.doctor_id.firstname} {instance.doctor_id.lastname}",
                'meet_link': instance.meeting_url,
                'from_date': instance.appointment_date,
                'from_time': instance.doctor_slot.slots if instance.doctor_slot else "",
                'to_date': None,
                'to_time': None,
                'description': None,
                'attachment': None,
                'participant_ids': "",
                'due_date': None
            }
    
        

        return data
    




class ReTaskStatusSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TaskStatus
        fields = ['id','status_name','fixed_state']
class TaskForRescheduleSerializer(serializers.ModelSerializer):
    status=ReTaskStatusSerializer()
    class Meta:
        model = Tasks
        fields = ['id','task_topic', 'due_date', 'status']
        


class TaskHierarchyForRescheduleSerializer(serializers.ModelSerializer):
    status=ReTaskStatusSerializer()
    class Meta:
        model = Tasks
        fields = ['id','task_topic', 'due_date', 'status']
# get when click on calender event

class GetSpecificUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id')
    class Meta:
        model = User
        fields = ['user_id','email','firstname','lastname','phone_no']
        
        
class GetSpecificEventsSerializer(serializers.ModelSerializer):
    user_id = GetSpecificUserSerializer()
    guest = GetSpecificUserSerializer(many = True)
    class Meta:
        model = Events
        fields = '__all__'


class GetSpecificTaskSerializer(serializers.ModelSerializer):
    created_by = GetSpecificUserSerializer()
    assign_to = GetSpecificUserSerializer(many = True)
    class Meta:
        model = Tasks
        fields = '__all__'
        
class GetSpecificMeetingCalenderSerializer(serializers.ModelSerializer):
    user_id              = GetSpecificUserSerializer()
    participant          = GetSpecificUserSerializer(many = True)
    class Meta:
        model = Meettings
        fields = '__all__'
        
    
        
class GetSpecificDoctorConsultationSerializer(serializers.ModelSerializer):
    doctor_id = GetSpecificUserSerializer()
    employee_id = GetSpecificUserSerializer()
    class Meta:
        model=DoctorConsultation
        fields = [ "doctor_id","employee_id",  "consultation_for", "appointment_date", "appointment_time" ,'reason_for_consultation', "meeting_pref_type"]

class MeetingSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeettingSummery
        fields = '__all__'


class GetSpecificTaskHierarchySerializer(serializers.ModelSerializer):
    created_by = GetSpecificUserSerializer()
    assign_to = GetSpecificUserSerializer(many = True)
    class Meta:
        model = TaskHierarchy
        fields = '__all__'

class TaskHierarchyCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskHierarchy
        exclude = ['created_by','assign_to']