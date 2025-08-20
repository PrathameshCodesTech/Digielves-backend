from digielves_setup.models import Helpdesk, HelpdeskAction
from rest_framework import serializers


class HelpdeskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = [
            'issue_raised_by', 'issue_subject', 'issue_description',
            'additional_info_for_support', 'preferred_support_contact',
            'organization', 'organization_branch'
        ]

class HelpdeskselfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = '__all__'
        depth=1

class HelpdeskRaisedActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpdeskAction
        fields = '__all__'

class HelpdeskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = '__all__'
        depth = 1