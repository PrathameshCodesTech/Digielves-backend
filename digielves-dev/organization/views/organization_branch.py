

from digielves_setup.models import DoctorPersonalDetails, OrganizationBranch, OrganizationDetails, EmployeePersonalDetails
from organization.seriallizers.organization_branch_seriallizer import EmployeeSerializer, GetOrganizationDetailsSerializer, OrganizationBranchSerializer, OrganizationDetailsSerializer, organizationBranchSerializer
from organization.seriallizers.organization_details_seriallizer import organizationDetailsSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Prefetch 

class OrgBranchViewSet(viewsets.ModelViewSet):

    serializer_class = organizationBranchSerializer
    
    

    
    @csrf_exempt
    def AddBranch(self, request):
        try:
            # Get the organization ID, branch name, and address from the request
            print("-------------------------")
            org_id = request.POST.get('org')
            branch_name = request.POST.get('branch_name')
            address = request.POST.get('Address')
    
            # Check if the organization with the provided ID exists
            print(org_id)
            org = OrganizationDetails.objects.get(user_id=org_id)
            print(org) 
            
    
            # Create a dictionary with the branch details
            branch_data = {
                'org': org,
                'branch_name': branch_name,
                'Address': address
            }
    
            # Create an instance of the organization branch using the dictionary
            org_branch = OrganizationBranch(**branch_data)
            org_branch.save()
    
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Branch created successfully.",
                "data": {
                    "org_id": org_id,
                    "branch_name": branch_name,
                    "address": address
                }
            })
    
        except OrganizationDetails.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Organization with the provided ID does not exist."
            })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })

        
    @csrf_exempt
    def get_organization_branch_by_user_and_org(self,request):
        print("--fggg-----")
        try:
            user_id = request.GET.get('user_id')
            #org_id = request.GET.get('org_id')

#            if not org_id:
#                return JsonResponse({
#                    "success": False,
#                    "status": status.HTTP_400_BAD_REQUEST,
#                    "message": "Invalid request. org_id is required."
#                    
#                })
            try:
                
                org = OrganizationDetails.objects.get(user_id=user_id)
                org_branches = OrganizationBranch.objects.filter(org_id=org)
    
                if not org_branches:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "No organization branches found for the given org_id and user_id."
                    })
    
            except Exception as e:
                print("-----heyyyyyeee")
                employeeDetails = EmployeePersonalDetails.objects.get(user_id=user_id)
                print(employeeDetails.organization_id)
                
                org = OrganizationDetails.objects.get(id=employeeDetails.organization_id.id)
                org_branches = OrganizationBranch.objects.filter(org_id=org)
                
                
            org_branch_serializer = organizationBranchSerializer(org_branches, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Organization branches retrieved successfully.",
                "data": org_branch_serializer.data
            })
            
                
                
                

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve organization branches.",
                "errors": str(e)
            })

    @csrf_exempt
    def get_organizations_nd_branch(self,request):
        try:
            user_id = request.GET.get('user_id')

            doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
            if not doctor:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "Doctor not found for the given user_id."
                })
            organizations = OrganizationDetails.objects.all()
            org_data = []
            print(organizations)
            for org in organizations:
                print(org)
                org_serializer = GetOrganizationDetailsSerializer(org)
                branches = OrganizationBranch.objects.filter(org=org)
                branch_serializer = OrganizationBranchSerializer(branches, many=True)
                print("----------")
                print(branch_serializer.data)
                org_data.append({
                    **org_serializer.data,
                    "branches": branch_serializer.data
                })
            return JsonResponse({
            "success": True,
            "status": 200,
            "message": "All organizations and their branches retrieved successfully.",
            "data": org_data
        })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Failed to retrieve organizations and their branches.",
                "errors": str(e)
            })
        # try:
        #     user_id = request.GET.get('user_id')

        #     doctor = DoctorPersonalDetails.objects.filter(user_id=user_id).first()
        #     if not doctor:
        #         return JsonResponse({
        #             "success": False,
        #             "status": 404,
        #             "message": "Doctor not found for the given user_id."
        #         })

        #     org = doctor.organization
        #     if not org:
        #         return JsonResponse({
        #             "success": False,
        #             "status": 404,
        #             "message": "Organization not found for the given user_id."
        #         })

        #     org_branches = OrganizationBranch.objects.filter(org=org)

        #     org_serializer = GetOrganizationDetailsSerializer(org)
        #     org_branch_serializer = organizationBranchSerializer(org_branches, many=True)

        #     data = {
        #         "organization": org_serializer.data,
        #         "branches": org_branch_serializer.data
        #     }

        #     return JsonResponse({
        #         "success": True,
        #         "status": 200,
        #         "message": "Organization and its branches retrieved successfully.",
        #         "data": data
        #     })

        # except Exception as e:
        #     return JsonResponse({
        #         "success": False,
        #         "status": 500,
        #         "message": "Failed to retrieve organization and its branches.",
        #         "errors": str(e)
        #     })
    
    @csrf_exempt
    def get_Employee_by_branch(self,request):

        try:
            user_id = request.GET.get('user_id')
            org_branch = request.GET.get('branch_id')
            try:
                
                org = OrganizationDetails.objects.get(user_id=user_id)
                branch = OrganizationBranch.objects.get(id=org_branch)
    
                if not org and not branch:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "No organization branches found for the given org_id and user_id."
                    })
                
                employeeDetails = EmployeePersonalDetails.objects.filter(organization_id=org,organization_location=branch, user_id__active=True, user_id__verified="1")
                employees = EmployeeSerializer(employeeDetails, many=True)
    
            except Exception as e:
                return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": str(e)
                    })

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Employee retrieved successfully.",
                "data": employees.data
            })
            

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Employe.",
                "errors": str(e)
            })