
from digielves_setup.models import OrganizationDetails, Policies
from organization.seriallizers.policy_seriallizers import GetPolicyRequestSerializer, GetSpecificPolicyRequestSerializer
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status

class RequestPolicyViewSet(viewsets.ModelViewSet):

    @csrf_exempt
    def get_requested_policy(self, request):
        try:
            user_id = request.GET.get('user_id')
            policy_id = request.GET.get('policy_id')
            
            org = OrganizationDetails.objects.get(user_id = user_id)
            if policy_id:
                policy = Policies.objects.get(pk=policy_id)
                serializer = GetSpecificPolicyRequestSerializer(policy)
                response = {
                "success": True,
                "status": 200,
                "data": serializer.data
                }

                return JsonResponse(response)
            else:
                
                policy = Policies.objects.filter(organization=org, policy_category = "New")
                serializer = GetPolicyRequestSerializer(policy, many=True)
                seriallized_date = serializer.data
                
                response = {
                "success": True,
                "status": 200,
                "data": seriallized_date
            }

            return JsonResponse(response)

        except Policies.DoesNotExist:
            return JsonResponse({'message': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)
