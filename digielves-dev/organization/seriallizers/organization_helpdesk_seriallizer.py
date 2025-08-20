from digielves_setup.models import EmployeePersonalDetails, Helpdesk, HelpdeskAction, HelpdeskAttachment
from rest_framework import serializers


class HelpdeskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = [
            'issue_raised_by', 'issue_assigned_to', 'issue_status',
            'issue_subject', 'issue_description', 'issue_priority',
            'issue_date', 'additional_info_for_support',
            'preferred_support_contact', 'organization', 'organization_branch'
        ]

class HelpdeskGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = '__all__'
        depth = 1


class HelpdeskndActionGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Helpdesk
        fields = '__all__'
        depth = 1


class HelpdeskAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpdeskAttachment
        fields = '__all__'

        
class EmployeePersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePersonalDetails
        fields = [
            'firstname', 'lastname', 'phone_no',
            'employee_id','user_id'
        ]
        depth =1



class HelpdeskndEmployeePersonalSerializer(serializers.ModelSerializer):
    helpdesk_attachments = HelpdeskAttachmentSerializer(many=True, source='helpdeskattachment_set')
    class Meta:
        model = Helpdesk
        exclude = ('issue_raised_by',)
        depth = 1
        

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        user_id = instance.issue_raised_by_id
        try:
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            data['issue_raised_by'] = EmployeePersonalDetailsSerializer(employee_details).data
        except EmployeePersonalDetails.DoesNotExist:
            data['issue_raised_by'] = None
        
        return data
    
    

# class HelpdeskndEmployeePersonalSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = Helpdesk
#         exclude = ('issue_raised_by',)
#         depth = 1
        

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
        
#         user_id = instance.issue_raised_by_id
#         try:
#             employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
#             data['issue_raised_by'] = EmployeePersonalDetailsSerializer(employee_details).data
#         except EmployeePersonalDetails.DoesNotExist:
#             data['issue_raised_by'] = None
        
#         return data



class HelpdeskActionndHelpdeskGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpdeskAction
        fields = '__all__'
        depth = 1


class HelpdeskActionGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpdeskAction
        fields = '__all__'