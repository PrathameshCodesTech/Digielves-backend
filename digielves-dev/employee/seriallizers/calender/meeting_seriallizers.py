from rest_framework import serializers

from digielves_setup.models import Events, Meettings, MeettingSummery
from configuration.onboardingEmail import sendMail
class Meettingerializer(serializers.ModelSerializer):
    other_participant_email = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Meettings
        exclude = ['participant']
        
    



class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meettings
        fields = '__all__'
        
class MeetingGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meettings
        fields = '__all__'
        #depth = 1


class MeettingSummerySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeettingSummery
        fields = ['meet_summery','meet_tasks']