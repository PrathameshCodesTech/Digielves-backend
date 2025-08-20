
from digielves_setup.models import Policies
from rest_framework import viewsets
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from employee.seriallizers.policy_seriallizers import  GetPolicySerializer, GetSpecificPolicySerializer, InsuredMemberSerializer, PolicySerializer


class PolicyViewSet(viewsets.ModelViewSet):   
    
    def add_policy(self, request):
        policy_data = request.data.copy()
        
        # Extract and parse insured members
        insured_members_json = policy_data.get('insured_members', '[]')
        print("🐍 File: policy/policy.py | Line: 18 | add_policy ~ insured_members_json",insured_members_json)
        
        insured_members_data = json.loads(insured_members_json)
        print("🐍 File: policy/policy.py | Line: 19 | add_policy ~ insured_members_data",insured_members_data)
        
        policy_serializer = PolicySerializer(data=policy_data)
        if policy_serializer.is_valid():
            # Save the policy instance
            policy_instance = policy_serializer.save()
            
            # Create InsuredMember instances
            for member_data in insured_members_data:
                print("🐍 File: policy/policy.py | Line: 28 | add_policy ~ member_data",member_data)
                member_data['policy'] = policy_instance.pk  # Assign policy foreign key
                insured_member_serializer = InsuredMemberSerializer(data=member_data)
                if insured_member_serializer.is_valid():
                    insured_member_serializer.save()
                else:
                    # If any member data is invalid, delete the policy instance and return error response
                    policy_instance.delete()
                    return JsonResponse(insured_member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Policy Created",
                "data": policy_serializer.data
            }
            
            return JsonResponse(response)
        else:
            response = {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": policy_serializer.errors
            }
            
            return JsonResponse(response)
        
    @csrf_exempt
    def get_policy(self, request):
        try:
            user_id = request.GET.get('user_id')
            policy_id = request.GET.get('policy_id')
            category = request.GET.get('category')
            if policy_id:
                policy = Policies.objects.get(pk=policy_id)
                serializer = GetSpecificPolicySerializer(policy)
                response = {
                "success": True,
                "status": 200,
                "data": serializer.data
                }

                return JsonResponse(response)
            else:

                policy = Policies.objects.filter(user=user_id)
                serializer = GetPolicySerializer(policy, many=True)
                seriallized_date = serializer.data
                
                response = {
                "success": True,
                "status": 200,
                "data": seriallized_date
            }

            return JsonResponse(response)

        except Policies.DoesNotExist:
            return JsonResponse({'message': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
