import base64
import random
from django.shortcuts import render
from configuration.authentication import JWTAuthenticationUser
from digielves_setup.models import Notification, OrganizationDetails, OrganizationSubscriptionRequest, User, OrganizationBranch, notification_handler
from organization.seriallizers.organization_details_seriallizer import GetMySubscriptionSerializer, organizationDetailsSerializer, UpdateOrganizationDetailsSerializer

from rest_framework import viewsets
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status


# Authentication Modules for rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.permissions import  IsAuthenticated ,AllowAny

from django.db.models import Max

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save


from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class OrganizationDetailsClass(viewsets.ModelViewSet):
    
    #authentication_classes = [JWTAuthenticationUser]
    #permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    throttle_classes = [AnonRateThrottle,UserRateThrottle]

    serializer_class =organizationDetailsSerializer
        
    # Client Registration API 
    @csrf_exempt
    def addOrganizationDetails(self,request):
        organizationDetails=OrganizationDetails()
        print("prem ki pujaran1")
        
        
        
        user=User.objects.get(id=request.data['user_id'], user_role="Dev::Organization")
        
        userAddressSerialData = organizationDetailsSerializer(organizationDetails,data=request.data)
           
            
        if userAddressSerialData.is_valid(raise_exception=True):
            
            userAddressSerialData.save()
            user.verified=1
            user.save()
            
            branch_name = request.data['branch_name']
            address = request.data['address']
            
            organization_details_instance = OrganizationDetails.objects.get(id=organizationDetails.id)
            
            organization_branch = OrganizationBranch(org=organization_details_instance, branch_name=branch_name, Address=address)
            organization_branch.save()
            
            

            return JsonResponse({
            "success": True,
            "status": status.HTTP_201_CREATED,                
            "message": "Organization Details added successfully",
            "data":
                {
                    "organization_id" : organizationDetails.id
                }
            })        
        #     except Exception as e:
        #         return JsonResponse({
        #                 "success": False,
        #                 "status": status.HTTP_400_BAD_REQUEST, 
        #                 "message": "Failed to add organization Details",
        #                 "errors": str(e)
        #                 })
        # except Exception as e:
        #         return JsonResponse({
        #                 "success": False,
        #                 "status": status.HTTP_400_BAD_REQUEST, 
        #                 "message": "Failed to add organization Details",
        #                 "errors": str(e)
        #                 })
                
    @csrf_exempt
    def updateOrganizationDetails(self,request):
        try:
            organizationDetails=OrganizationDetails.objects.get(id = request.data['organization_id'])

            userAddressSerialData = UpdateOrganizationDetailsSerializer(organizationDetails,data=request.data)
            try:
                
                if userAddressSerialData.is_valid(raise_exception=True):
                    userAddressSerialData.save()

                    return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Organization Details added successfully",
                    "data":
                        {
                            "organization_id" : organizationDetails.id
                        }
                    })        
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add organization Details",
                        "errors": str(e)
                        })
        except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST, 
                        "message": "Failed to add organization Details",
                        "errors": str(e)
                        })

class SubscriptionClass(viewsets.ModelViewSet):
    

    @csrf_exempt
    def make_request_for_subscription(self,request):
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id, user_role="Dev::Organization")

            if user:
                organization_details = OrganizationDetails.objects.get(user_id=user)
                user_admin = User.objects.get(user_role="Dev::Admin")

                subscription_want = request.data.get('subscription_want')

                subscription_request = OrganizationSubscriptionRequest.objects.create(
                    organization=organization_details,
                    subscription_before=organization_details.number_of_subscription,
                    subscription_want=subscription_want,
                    approver=user_admin
                )
                
                
                try:
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=request.user,
                        where_to="request",
                        notification_msg = f"{organization_details.name} has requested a subscription change. Please review and take appropriate action.",
                        action_content_type=ContentType.objects.get_for_model(OrganizationSubscriptionRequest),
                        action_id=subscription_request.id
                    )
                    
                    notification.notification_to.add(user_admin.id)
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    
                except Exception as e:
                    print("Notification creation failed:", e)


                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Subscription request created successfully"
                })

            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "You don't have permission"
                })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found"
            })

        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization details not found"
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to make a subscription request",
                "errors": str(e)
            })
            
    @csrf_exempt
    def get_my_request(self, request):
        user_id = request.GET.get('user_id')

        
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Organization":
            organization_details = OrganizationDetails.objects.get(user_id=user)
            
            subscription=OrganizationSubscriptionRequest.objects.filter(organization=organization_details)
            
            seriallized_data = GetMySubscriptionSerializer(subscription,many=True)
            
            return JsonResponse({
                    "success": True,
                    "status": 200,
                    "message": "Subscription retrieved Successfully",
                    "data": seriallized_data.data
                })
            
        
        return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "You don't have permission"
                })