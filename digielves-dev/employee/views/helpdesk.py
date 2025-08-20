

from django.http import JsonResponse

from configuration.gzipCompression import compress
from digielves_setup.models import Helpdesk, HelpdeskAction, HelpdeskAttachment, User
from employee.seriallizers.helpdesk_seriallizer import HelpdeskCreateSerializer, HelpdeskRaisedActionSerializer, HelpdeskSerializer, HelpdeskselfSerializer
from organization.seriallizers.organization_helpdesk_seriallizer import HelpdeskActionndHelpdeskGetSerializer, HelpdeskndEmployeePersonalSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings

class HelpdeskViewSet(viewsets.ModelViewSet):
    serializer_class = HelpdeskCreateSerializer


    @csrf_exempt
    def raise_issue(self, request):
        print(request.data)
        try:
            serializer = HelpdeskCreateSerializer(data=request.data)
            if serializer.is_valid():
                helpDesk=serializer.save()
                attachments = request.FILES.getlist('attachments') 
                print("-----------------")
                print(attachments)
                helpdesk_attachments = []
                for attachment in attachments:
                    try:
                        
                        file_name = attachment.name
                        file_path = 'employee/helpdesk_attachments/' + file_name
                        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
                        saved_file = fs.save(file_path, attachment)
                        
                        helpdesk_attachment = HelpdeskAttachment.objects.create(helpdesk=helpDesk, attachment=saved_file)
                        helpdesk_attachments.append(helpdesk_attachment)
                    except Exception as e:
                        print(e)
                        pass
                    #     return JsonResponse({
                    #     "success": False,
                    #     "status": status.HTTP_400_BAD_REQUEST,
                    #     "message": "Failed to create Task.",
                    #     "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
                    # })

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Issue raised successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to raise issue.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while raising the issue.",
                "errors": str(e)
            })
        
    @csrf_exempt
    def get_raised_issue(self, request):
        try:
            user_id = request.query_params.get('user_id')
            

            queryset = Helpdesk.objects.all()

            if user_id:
                queryset = queryset.filter(issue_raised_by=user_id)
            else:
                queryset=queryset

            serializer = HelpdeskselfSerializer(queryset, many=True)

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
    def get_assigned_issue(self, request):
        
        user_id = request.query_params.get('user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is required."
            })

        helpdesk_instances = Helpdesk.objects.filter(issue_assigned_to=user_id)
        serializer = HelpdeskSerializer(helpdesk_instances, many=True)

        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Helpdesk instances retrieved successfully.",
            "data": serializer.data
        })
    



    @csrf_exempt
    def get_issues_nd_action(self, request):
        try:
            helpdesk_id = request.GET.get('helpdesk_id')
            user_id = request.GET.get('user_id')


            
            helpdesk = Helpdesk.objects.get(id=helpdesk_id)
            helpdesk_serializer = HelpdeskndEmployeePersonalSerializer(helpdesk)


            # is_assigned_to_user = helpdesk.issue_assigned_to.filter(id=user_id).exists()
            # is_raised_by_user = helpdesk.issue_raised_by.id == user_id if helpdesk.issue_raised_by else False
            
            # if not (is_assigned_to_user or is_raised_by_user):
            #     return JsonResponse({
            #         "success": False,
            #         "status": status.HTTP_401_UNAUTHORIZED,
            #         "message": "Unauthorized access to helpdesk details and actions."
            #     })
            
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
    
class HelpdeskActionViewSet(viewsets.ModelViewSet):
    serializer_class = HelpdeskRaisedActionSerializer

    @csrf_exempt
    def raise_issue_action(self, request):
        print(request.data)
        try:
            user_id = request.data.get('user_id')
            helpdesk_id = request.data.get('helpdesk_id')
            remark = request.data.get('remark')

            if not (user_id and helpdesk_id and remark):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id, helpdesk_id, and remark are required."
                })

            helpdesk = Helpdesk.objects.get(id=helpdesk_id, issue_assigned_to=user_id)
            
            print(helpdesk)
            user = User.objects.get(id=user_id)
            print(user.id)

            helpdesk_action = HelpdeskAction(user=user, helpdesk=helpdesk, remark=remark)
            helpdesk_action.save()
            assigned_users = helpdesk.issue_assigned_to.all()
            print(HelpdeskAction.objects.filter(user__in=assigned_users, helpdesk=helpdesk).count())
            print(assigned_users.count())
            if assigned_users.count() == HelpdeskAction.objects.filter(user__in=assigned_users, helpdesk=helpdesk).count():
                helpdesk.issue_status = "Solved"
                helpdesk.save()

            serializer = HelpdeskRaisedActionSerializer(helpdesk_action)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Helpdesk action created successfully.",
                "data": serializer.data
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
                "message": "Failed to create helpdesk action.",
                "errors": str(e)
            })
    


    
    
    

        