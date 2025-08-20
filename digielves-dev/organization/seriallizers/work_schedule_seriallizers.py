from digielves_setup.models import OrganizationWorkSchedule, Weekday
from rest_framework import serializers

class WeekdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Weekday
        fields = ['name']
        
        
class OrganizationWorkScheduleSerializer(serializers.ModelSerializer):
    weekdays = WeekdaySerializer(many=True, read_only=True, source='weekday_set')
    class Meta:
        model = OrganizationWorkSchedule
        fields = ['start_time', 'end_time', 'working_hours', 'weekdays']
        