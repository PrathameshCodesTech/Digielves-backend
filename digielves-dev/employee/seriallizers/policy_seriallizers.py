from digielves_setup.models import EmployeePersonalDetails, InsuredMember, Policies, PolicyDocument
from rest_framework import serializers

class InsuredMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuredMember
        fields = ['name', 'dob', 'gender', 'relationship_to_policyholder']

class PolicyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyDocument
        fields = ['document_name', 'document_file']

class PolicySerializer(serializers.ModelSerializer):
    # insured_members = InsuredMemberSerializer(many=True, required=False)
    # documents = PolicyDocumentSerializer(many=True, required=False)

    class Meta:
        model = Policies
        fields = '__all__'
        
        
    def create(self, validated_data):
        user_id = validated_data.get('user')

        try:
            employee_organization = EmployeePersonalDetails.objects.get(user_id=user_id)

            if employee_organization.organization_id:
                organization_id = employee_organization.organization_id.id
            else:
                organization_id = None

            validated_data['organization_id'] = organization_id

            return super().create(validated_data)

        except EmployeePersonalDetails.DoesNotExist:
            raise serializers.ValidationError("Employee personal details not found for the provided user ID")

        except Exception as e:
            raise serializers.ValidationError(str(e))


class InsuredMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuredMember
        fields = '__all__'
    # def create(self, validated_data):
    #     insured_members_data = validated_data.pop('insured_members', [])
    #     documents_data = validated_data.pop('documents', [])

    #     policy = Policy.objects.create(**validated_data)

    #     for member_data in insured_members_data:
    #         InsuredMember.objects.create(policy=policy, **member_data)

    #     for document_data in documents_data:
    #         PolicyDocument.objects.create(policy=policy, **document_data)

    #     return policy

class GetPolicySerializer(serializers.ModelSerializer):


    class Meta:
        model = Policies
        fields = '__all__'
        

class GetSpecificPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policies
        fields = '__all__'
        