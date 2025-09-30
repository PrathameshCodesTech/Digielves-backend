from digielves_setup.models import Events, Meettings, Tasks, User,DoctorConsultation
from rest_framework import serializers


class ShowDoctorConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorConsultation
        fields = '__all__'
        depth = 2
        
        
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task_topic', 'due_date']


class CombinedEventMeetingSerializerForAddOns(serializers.Serializer):
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
    status=serializers.CharField()
    
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
                'due_date': None,
                'status':None
            }
        elif isinstance(instance, Meettings):
            data = {
                'category': 'Meeting',
                'id': instance.id,
                'title': instance.title,
                'from_date': instance.from_date,
                'from_time': instance.from_time,
                'to_date': instance.to_date,
                'to_time': instance.to_time,
                'meet_link': instance.meet_link,
                'description': instance.purpose,
                'attachment': None,
                'participant_ids': list(instance.participant.values_list('id', flat=True)),
                'due_date': None,
                'status':None
            }
        elif isinstance(instance, Tasks):
            data = {
                'category': 'Task',
                'id': instance.id,
                'title': instance.task_topic,
                'from_date': None,
                'from_time': None,
                'to_date': None,
                'to_time': None, 
                'description': instance.task_description,
                'attachment': None, 
                'assign_to_ids': list(instance.assign_to.values_list('id', flat=True)),
                'due_date': instance.due_date,
                'status':""
            }
        else:
            data = {}

        return data


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
    
        else:
            data = {}

        return data