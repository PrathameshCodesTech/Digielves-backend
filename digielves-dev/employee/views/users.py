


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from employee.seriallizers.user_serillizer import GetPersonalDetailsSerializer
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import ObjectDoesNotExist
from configuration.gzipCompression import compress
from digielves_setup.models import EmployeePersonalDetails, OutsiderUser, User
from django.db.models import Q

class UserViewSet(viewsets.ModelViewSet):



    @csrf_exempt
    def get_users(self,request):
        user_id = request.GET.get('user_id')
        show_outsider = request.GET.get('os')
        

        try:
            print(user_id)
            user = User.objects.get(id=user_id)
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            
            user_data = []
            if employee_details:
                users = User.objects.filter(employeepersonaldetails__organization_id=employee_details.organization_id,
                                            employeepersonaldetails__organization_location=employee_details.organization_location, 
                                            verified=1,
                                            user_role="Dev::Employee"
                                            ,active=True).exclude(id=user_id)
              
                for user in users:
                    employee_details = EmployeePersonalDetails.objects.filter(user_id=user.id).first()
                    user_profile_picture = getattr(employee_details, 'profile_picture', None) 
                    user_data.append({
                        'user_id': user.id,
                        'email': user.email,
                        'firstname': user.firstname,
                        'lastname': user.lastname,
                        'phone_no': user.phone_no,
                        'profile_picture': user_profile_picture
                    })
            if show_outsider == "False" or show_outsider == "false":
                pass
            else:

                outsiders = OutsiderUser.objects.filter(added_by=user_id)
                outsiders_secondary_related = OutsiderUser.objects.filter(secondary_adders__in=[user_id])

                outsiders = OutsiderUser.objects.filter(Q(added_by=user_id) | Q(secondary_adders__in=[user_id]))

                if outsiders or outsiders_secondary_related:
                    
                    related_user_ids = outsiders.values_list('related_id', flat=True)
                    all_related_users = User.objects.filter(id__in=related_user_ids, verified=1)

                    for user in all_related_users:
                        user_profile_picture = getattr(user, 'profile_picture', None) 
                        user_data.append({
                            'user_id': user.id,
                            'email': user.email,
                            'firstname': user.firstname,
                            'lastname': user.lastname,
                            'phone_no': user.phone_no,
                            'outsider': True,
                            'profile_picture': user_profile_picture
                        })
                    
                response = {
                    'success': True,
                    'status': 200,
                    'message': 'Users fetched successfully.',
                    'data': user_data
                }

                return compress(response)
         
            response = {
                'success': True,
                'status': 200,
                'message': 'Users fetched successfully.',
                'data': user_data
            }

            return JsonResponse(response)
        except ObjectDoesNotExist:
            response = {
                'success': False,
                'status': 404,
                'message': 'User not found or not verified.',
            }

            return JsonResponse(response)
        except Exception as e:
            response = {
                'success': False,
                'status': 500,
                'message': 'An error occurred while fetching users.',
                'error': str(e)
            }

            return JsonResponse(response)

    @csrf_exempt
    def get_users_details(self,request):
        user_id = request.GET.get('user_id')
        

        try:
            user = User.objects.get(id=user_id)
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)
            seriallized_data = GetPersonalDetailsSerializer(employee_details)

            response = {
                    'success': True,
                    'status': 200,
                    'message': 'Users fetched successfully.',
                    'data': seriallized_data.data
                }

            return compress(response)
        
        except ObjectDoesNotExist:
            response = {
                'success': False,
                'status': 404,
                'message': 'User not found or not verified.',
            }

            return JsonResponse(response)
        except Exception as e:
            response = {
                'success': False,
                'status': 500,
                'message': 'An error occurred while fetching users.',
                'error': str(e)
            }

            return JsonResponse(response)
