from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import EmployeePersonalDetails, Helpdesk, HelpdeskAction, User

from organization.seriallizers.organization_helpdesk_seriallizer import HelpdeskActionGetSerializer, HelpdeskActionndHelpdeskGetSerializer, HelpdeskGetSerializer, HelpdeskUpdateSerializer, HelpdeskndActionGetSerializer, HelpdeskndEmployeePersonalSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class HelpDeskViewSet(viewsets.ModelViewSet):
    serializer_class = HelpdeskUpdateSerializer
    
    @csrf_exempt
    def updateHelpdesk(self, request):
            try:
                helpdesk_id = request.data.get('helpdesk_id')
                organization_id = request.data.get('organization_id')

                if not (helpdesk_id and organization_id):
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid request. helpdesk_id and organization_id are required."
                    })

                helpdesk = Helpdesk.objects.get(id=helpdesk_id, organization_id=organization_id)
                print(helpdesk)

                issue_assigned_to_ids = request.data.get('issue_assigned_to_ids')
                if issue_assigned_to_ids is not None:
                    issue_assigned_to_ids = [int(user_id) for user_id in issue_assigned_to_ids.split(',') if user_id.isdigit()]
                    issue_assigned_to_users = User.objects.filter(id__in=issue_assigned_to_ids)
                    helpdesk.issue_assigned_to.set(issue_assigned_to_users)
                # if issue_assigned_to_ids is not None:
                #     issue_assigned_to_users = User.objects.filter(id__in=issue_assigned_to_ids)
                #     helpdesk.issue_assigned_to.set(issue_assigned_to_users)

                issue_status = request.data.get('issue_status')
                if issue_status is not None:
                    helpdesk.issue_status = issue_status

                issue_priority = request.data.get('issue_priority')
                if issue_priority is not None:
                    helpdesk.issue_priority = issue_priority
                

                comment_box = request.data.get('comment')
                if comment_box is not None:
                    helpdesk.comment_box = comment_box

                helpdesk.save()

                serializer = HelpdeskUpdateSerializer(helpdesk)

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Helpdesk issue updated successfully.",
                    "data": serializer.data
                })

            except Helpdesk.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Helpdesk issue not found.",
                })
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "Failed to update helpdesk issue.",
                    "errors": str(e)
                })
    



    @csrf_exempt
    def get_raised_issue(self, request):
        try:
            
            organization_id = request.query_params.get('organization_id')

            queryset = Helpdesk.objects.all()
            queryset = queryset.filter(organization=organization_id)
            

            serializer = HelpdeskGetSerializer(queryset, many=True)

            return JsonResponse({
                        "success": True,
                        "status": status.HTTP_201_CREATED,
                        "message": "Issue raised get successfully.",
                        "data": serializer.data
                    })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while retrieving issues.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def get_issues_nd_action(self, request):
        try:
            helpdesk_id = request.GET.get('helpdesk_id')
            organization_id = request.GET.get('organization_id')
            helpdesk = Helpdesk.objects.get(id=helpdesk_id, organization_id=organization_id)
            helpdesk_serializer = HelpdeskndEmployeePersonalSerializer(helpdesk)

            helpdesk_actions = HelpdeskAction.objects.filter(helpdesk=helpdesk)
            helpdesk_actions_serializer = HelpdeskActionndHelpdeskGetSerializer(helpdesk_actions, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Helpdesk details and actions retrieved successfully.",
                "data": {
                    "helpdesk": helpdesk_serializer.data,
                    "helpdesk_actions": helpdesk_actions_serializer.data
                }
            })

        except Helpdesk.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Helpdesk not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve helpdesk details and actions.",
                "errors": str(e)
            })

    @csrf_exempt
    def get_users(self, request):
        user_id = request.GET.get('organization_id')
        helpdesk_id = request.GET.get('helpdesk_id')
        

        try:
            # user = User.objects.get(id=user_id)
            # employee_details = EmployeePersonalDetails.objects.filter(organization_id=user_id)

            # if not employee_details.exists():
            #     response = {
            #         'success': False,
            #         'status': 403,
            #         'message': 'User does not have access to the specified organization.',
            #     }
            #     return JsonResponse(response)

            try:
                helpdesk = Helpdesk.objects.get(id=helpdesk_id)
     

                assigned_users = helpdesk.issue_assigned_to.all()
                created_by_user = helpdesk.issue_raised_by
                users = User.objects.filter(employeepersonaldetails__organization_id=user_id, verified=1,user_role="Dev::Employee").exclude(id__in=assigned_users).exclude(id=created_by_user.id)

                user_data = []
                for user in users:
                    user_data.append({
                        'user_id': user.id,
                        'email': user.email,
                        'firstname': user.firstname,
                        'lastname': user.lastname,
                        'phone_no': user.phone_no,
                    })

                response = {
                    'success': True,
                    'status': 200,
                    'message': 'Users fetched successfully.',
                    'data': user_data
                }

                return compress(response)

            except Helpdesk.DoesNotExist:
                response = {
                    'success': False,
                    'status': 404,
                    'message': 'Board not found.',
                }
                return JsonResponse(response)

        except User.DoesNotExist:
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

class HelpDeskActionViewSet(viewsets.ModelViewSet):
    serializer_class = HelpdeskGetSerializer

    @csrf_exempt
    def get_helpdesk_actions(self, request):

        helpdesk_id = request.GET.get('helpdesk_id')
        organization_id = request.GET.get('organization_id')

        if not (helpdesk_id and organization_id):
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. helpdesk_id and organization_id are required."
            })
        # helpdesk = Helpdesk.objects.get(id=helpdesk_id, organization_id=organization_id)

        # helpdesk_actions = HelpdeskAction.objects.filter(helpdesk_id=helpdesk_id)
        # serializer = HelpdeskActionGetSerializer(helpdesk_actions, many=True)
        try:
            helpdesk = Helpdesk.objects.get(id=helpdesk_id, organization_id=organization_id)
            helpdesk_actions = HelpdeskAction.objects.filter(helpdesk_id=helpdesk_id)
            serializer = HelpdeskActionGetSerializer(helpdesk_actions, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Helpdesk actions retrieved successfully.",
                "data": serializer.data
            })
        except Helpdesk.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Helpdesk action not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve helpdesk actions.",
                "errors": str(e)
            })