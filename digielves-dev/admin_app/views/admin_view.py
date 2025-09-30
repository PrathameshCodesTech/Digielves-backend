

from digielves_setup.models import Notification, OrganizationDetails, OrganizationSubscriptionRequest, User, DoctorPersonalDetails, OrganizationBranch, notification_handler

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets
from admin_app.seriallizers.admin_seriallizers import GetSubscriptionSerializer, OrganizationDetailsSerializer, DoctorDetailsSerializer, OrganizationSerializer, branchesSerializerForSpecific, OrganizationUpdateDetailsSerializer, OrganizationSpecificDetailsSerializer, DoctorDpecificDetailsSerializer
from admin_app.seriallizers.admin_seriallizers import GetSubscriptionSerializer, OrganizationDetailsSerializer, DoctorDetailsSerializer, branchesSerializerForSpecific, OrganizationUpdateDetailsSerializer, OrganizationSpecificDetailsSerializer, DoctorDpecificDetailsSerializer

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save


class OrganizationDetailsViewSet(viewsets.ModelViewSet):

    serializer_class = OrganizationDetailsSerializer

    @csrf_exempt
    def getOrganizations(self, request):
        
        user_id = request.GET.get('user_id')

        if user_id:
            try: 
                user = User.objects.get(id=user_id)
                
                print(user.user_role)
                if user.user_role == "Dev::Admin":
                    organization_details = OrganizationDetails.objects.all()
                    serializer = OrganizationDetailsSerializer(organization_details,many=True)
                    response={
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Organizations retrieved successfully.",
                    "data": serializer.data,
            
                }
                    
                    return JsonResponse(response,safe=False)
            
                else:
                    return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)
            except OrganizationDetails.DoesNotExist:
                return JsonResponse({"success": False,'message': 'OrganizationDetails not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({"success": False,'message': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            

    @csrf_exempt
    def getspecificOrganizationDetails(self,request):
        organization_id = request.GET.get('organization_id')
        user_id = request.GET.get('user_id')
    
        if user_id:
            try:
                user = User.objects.get(id=user_id)
    
                if organization_id:
                    try:
                        organization = OrganizationDetails.objects.get(id=organization_id)
                        print(organization.id)
                        organization_branch = OrganizationBranch.objects.filter(org=organization)
                        serializer = OrganizationSpecificDetailsSerializer(organization)
                        branches_data = []
    
                        for branch in organization_branch:
                            branch_data = {
                                "branch_name": branch.branch_name,
                                "Address": branch.Address
                            }
                            branches_data.append(branch_data)
    
                        response = {
                            "success": True,
                            "status": status.HTTP_200_OK,
                            "message": "Organization retrieved successfully.",
                            "data": serializer.data,
                            "branches": branches_data
                        }
                        return JsonResponse(response)
                    except OrganizationDetails.DoesNotExist:
                        return JsonResponse(
                            {"success": False, 'message': 'Organization not found with the provided organization_id'},
                            status=status.HTTP_404_NOT_FOUND
                        )
                else:
                    return JsonResponse(
                        {"success": False, 'message': 'organization_id is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except OrganizationDetails.DoesNotExist:
                return JsonResponse(
                    {"success": False, 'message': 'OrganizationDetails not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return JsonResponse(
                {"success": False, 'message': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

            

    @csrf_exempt
    def deleteOrganization(self, request):
        user_id = request.GET.get('user_id')
        organization_id = request.GET.get('organization_id')
        
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Admin":
        
            if organization_id:
                try:
                    organization = OrganizationDetails.objects.get(id=organization_id)
                    
                    user_id = organization.user_id_id
                    User.objects.filter(id=user_id).delete()
    
                    organization.delete()
    
                    return JsonResponse({"success": True, 'message': 'Organization and associated User deleted successfully'}, status=status.HTTP_200_OK)
                except OrganizationDetails.DoesNotExist:
                    return JsonResponse({"success": False, 'message': 'Organization not found with the provided ID'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"success": False, 'message': 'organization_id is required'}, status=status.HTTP_400_BAD_REQUEST)
      
        else:
            return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)    
            
    @csrf_exempt
    def updateOrganization(self, request):
        user_id = request.data.get('auth_user_id')
        organization_id = request.data.get('organization_id')
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Admin":
            if organization_id:
                try:
                    organization = OrganizationDetails.objects.get(id=organization_id)
                    serializer = OrganizationUpdateDetailsSerializer(organization, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({"success": True, 'message': 'OrganizationDetails updated successfully'}, status=status.HTTP_200_OK)
                    else:
                        return JsonResponse({"success": False, 'message': 'Invalid data provided for update'}, status=status.HTTP_400_BAD_REQUEST)
                except OrganizationDetails.DoesNotExist:
                    return JsonResponse({"success": False, 'message': 'Organization not found with the provided organization_id'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"success": False, 'message': 'organization_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)
            


    @csrf_exempt
    def getOrganizationsName(self, request):
        
        user_id = request.GET.get('user_id')

        if user_id:
            try: 
                user = User.objects.get(id=user_id)
                
                print(user.user_role)
                if user.user_role == "Dev::Admin":
                    organization_details = OrganizationDetails.objects.filter(user_id__active=True)
                    serializer = OrganizationSerializer(organization_details,many=True)
                    response={
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Organizations retrieved successfully.",
                    "data": serializer.data,
            
                }
                    
                    return JsonResponse(response,safe=False)
            
                else:
                    return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)
            except OrganizationDetails.DoesNotExist:
                return JsonResponse({"success": False,'message': 'OrganizationDetails not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({"success": False,'message': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)


class DoctorDetailsViewSet(viewsets.ModelViewSet):

    #serializer_class = OrganizationDetailsSerializer

    @csrf_exempt
    def getDoctors(self, request):
        
        user_id = request.GET.get('user_id')

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                
                print(user.user_role)
                if user.user_role == "Dev::Admin":
                    doctor_details = DoctorPersonalDetails.objects.all()
                    serializer = DoctorDetailsSerializer(doctor_details,many=True)
                    response={
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Doctors retrieved successfully.",
                    "data": serializer.data,
            
                }
                    
                    return JsonResponse(response,safe=False)
            
                else:
                    return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)
            except OrganizationDetails.DoesNotExist:
                return JsonResponse({"success": False,'message': 'Doctors not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({"success": False,'message': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            


    @csrf_exempt
    def getspecificDoctorDetails(self, request):
        doctor_id = request.GET.get('doctor_id')
        user_id = request.GET.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if doctor_id:
                    try:
                        doctor = DoctorPersonalDetails.objects.get(id=doctor_id)
                        serializer = DoctorDpecificDetailsSerializer(doctor)
                        response={
                              "success": True,
                              "status": status.HTTP_200_OK,
                              "message": "Doctor retrieved successfully.",
                              "data": serializer.data,
                      
                          }
                        return JsonResponse(response)
                    except OrganizationDetails.DoesNotExist:
                        return JsonResponse({"success": False, 'message': 'Doctor not found with the provided organization_id'}, status=status.HTTP_404_NOT_FOUND)
                else:
                    return JsonResponse({"success": False, 'message': 'dector_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            except OrganizationDetails.DoesNotExist:
                return JsonResponse({"success": False,'message': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({"success": False,'message': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            


    
    @csrf_exempt
    def deleteDoctor(self, request):
        user_id = request.GET.get('user_id')
        doctor_id = request.GET.get('doctor_id')
        
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Admin":
        
            if doctor_id:
                try:
                    doctor = DoctorPersonalDetails.objects.get(id=doctor_id)
                    
                    user_id = doctor.user_id_id
                    User.objects.filter(id=user_id).delete()
    
                    doctor.delete()
    
                    return JsonResponse({"success": True, 'message': 'Doctor and associated User deleted successfully'}, status=status.HTTP_200_OK)
                except OrganizationDetails.DoesNotExist:
                    return JsonResponse({"success": False, 'message': 'Doctor not found with the provided ID'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"success": False, 'message': 'doctor_id is required'}, status=status.HTTP_400_BAD_REQUEST)
      
        else:
            return JsonResponse({"success": False,'message': "you don't have permission"}, status=401)    
            
            




class OrganizationSubscriptionRequestViewSet(viewsets.ModelViewSet):

    serializer_class = OrganizationDetailsSerializer
    
    
    
    @csrf_exempt
    def get_request(self, request):
        user_id = request.GET.get('user_id')

        
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Admin":
            
            subscription=OrganizationSubscriptionRequest.objects.all()
            
            seriallized_data = GetSubscriptionSerializer(subscription,many=True)
            
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Subscription retrieved Successfully",
                    "data": seriallized_data.data
                })
            
        
        return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "You don't have permission"
                })
    
    @csrf_exempt
    def manage_request(self, request):
        user_id = request.data.get('user_id')
        subscription_id = request.data.get('subscription_id')
        phase = request.data.get('accept')
        
        user = User.objects.get(id=user_id)
        if user.user_role == "Dev::Admin":
            
            subscription=OrganizationSubscriptionRequest.objects.get(id = subscription_id)
            
            if phase=="2":
                subscription.approval_phase=phase
                subscription.approved=False
                organization_details = OrganizationDetails.objects.get(id=subscription.organization.id)
                try:
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=request.user,
                        where_to="request",
                        notification_msg = f"Your subscription change request has been declined by the admin. We appreciate your understanding and cooperation.",
                        action_content_type=ContentType.objects.get_for_model(OrganizationSubscriptionRequest),
                        action_id=subscription.id
                    )
                    
                    notification.notification_to.add(organization_details.user_id)
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    
                except Exception as e:
                    print("Notification creation failed:", e)
            else:
                subscription.approved=True
                subscription.approval_phase=phase
                organization_details = OrganizationDetails.objects.get(id=subscription.organization.id)
                organization_details.number_of_subscription+=subscription.subscription_want
                organization_details.save()
                
                try:
                    post_save.disconnect(notification_handler, sender=Notification)
                    notification = Notification.objects.create(
                        user_id=request.user,
                        where_to="request",
                        notification_msg = f"Your subscription change request has been approved by the admin. Thank you for your cooperation.",
                        action_content_type=ContentType.objects.get_for_model(OrganizationSubscriptionRequest),
                        action_id=subscription.id
                    )
                    
                    notification.notification_to.add(organization_details.user_id)
                    post_save.connect(notification_handler, sender=Notification)
                    post_save.send(sender=Notification, instance=notification, created=True)
                    
                except Exception as e:
                    print("Notification creation failed:", e)
            subscription.save()
            return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Subscription Updated Successfully"
                })
            
        
        return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "You don't have permission"
                })
            
            
            
        