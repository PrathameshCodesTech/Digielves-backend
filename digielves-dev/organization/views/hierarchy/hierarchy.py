import random
from django.http import JsonResponse
from configuration.gzipCompression import compress

from digielves_setup.models import EmployeePersonalDetails, OrganizationDetails, ReportingRelationship, User, UserCreation, UserPosition
from organization.seriallizers.hierarchy_seriallizers import HierarchyUserCreationSerializer, HierarchyUserSerializer
from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import json
class TreeHierarchyViewSet(viewsets.ModelViewSet):
    
    

    @csrf_exempt
    def get_reporting_tree(self, request):
        try:
            user_id = request.GET.get("user_id")
            if not user_id:
                return JsonResponse({"success": False, "status": 400, "message": "Missing user_id."}, status=400)
    
            user_instance = User.objects.get(id=user_id)
            organization = OrganizationDetails.objects.get(user_id=user_instance.id)
            
            # Fetch users and positions
            all_users = UserCreation.objects.filter(organization_id=organization)
            user_map = {user.id: user for user in all_users}
            
            # Fetch designations
            designation_map = {}
            for user in all_users:
                designation = None
                if user.employee_user_id:
                    try:
                        designation = EmployeePersonalDetails.objects.get(user_id=user.employee_user_id.id).designation
                    except EmployeePersonalDetails.DoesNotExist:
                        pass
                designation_map[user.id] = designation
            
            # Fetch relationships
            relationships = ReportingRelationship.objects.select_related("reporting_user", "reporting_to_user").filter(
                reporting_user__organization_id=organization,
                reporting_to_user__organization_id=organization
            )
            
            # Build manager-to-employees map (supports multiple reporting relationships)
            manager_to_employees = {}
            for rel in relationships:
                manager_id = rel.reporting_to_user.id
                employee_id = rel.reporting_user.id
                if manager_id not in manager_to_employees:
                    manager_to_employees[manager_id] = []
                if employee_id not in manager_to_employees[manager_id]:
                    manager_to_employees[manager_id].append(employee_id)
            
            # Build employees-to-managers map
            employee_to_managers = {}
            for rel in relationships:
                manager_id = rel.reporting_to_user.id
                employee_id = rel.reporting_user.id
                if employee_id not in employee_to_managers:
                    employee_to_managers[employee_id] = []
                if manager_id not in employee_to_managers[employee_id]:
                    employee_to_managers[employee_id].append(manager_id)
            
            # Find top-level users (no managers)
            top_level_users = []
            for user_id in user_map:
                if user_id not in employee_to_managers:
                    top_level_users.append(user_id)
            
            # Keep track of users that have been processed to avoid duplicates
            processed_users = set()
            
            # Build the tree structure
            def build_node(user_id, parent_chain=None):
                if parent_chain is None:
                    parent_chain = []
                
                # Avoid circular references
                if user_id in parent_chain:
                    return None
                
                user = user_map[user_id]
                node = {
                    "id": user.id,
                    "email": user.email,
                    "designation": designation_map.get(user.id)
                }
                
                # Add to processed users
                processed_users.add(user_id)
                
                current_chain = parent_chain + [user_id]
                
                # Find all direct reports
                if user_id in manager_to_employees:
                    children_nodes = []
                    for child_id in manager_to_employees[user_id]:
                        # Avoid adding a node that would create a loop
                        if child_id not in current_chain:
                            child_node = build_node(child_id, current_chain)
                            if child_node:
                                children_nodes.append(child_node)
                    
                    if children_nodes:
                        node["children"] = children_nodes
                
                return node
            
            # Create the organizational root node
            result = {
                "id": "org",
                "email": organization.name,
                "children": [build_node(user_id) for user_id in top_level_users]
            }
            
            # Handle specific multi-reporting relationships
            # We process these after the main tree to avoid duplication
            
            # Add nodes for users with multiple reporting relationships
            for rel in relationships:
                manager_id = rel.reporting_to_user.id
                employee_id = rel.reporting_user.id
                
                # If this is a secondary reporting relationship (employee already has a main manager)
                if employee_id in processed_users:
                    # We need to find the manager node and add the employee as a child
                    def find_manager_and_add_child(node, manager_id, employee_id):
                        if node["id"] == manager_id:
                            if "children" not in node:
                                node["children"] = []
                            
                            # Check if this employee is already a child of this manager
                            existing_child = next((c for c in node["children"] if c["id"] == employee_id), None)
                            if not existing_child:
                                # Create a simplified child node without its own children
                                # to avoid duplication in the tree
                                child_node = {
                                    "id": employee_id,
                                    "email": user_map[employee_id].email,
                                    "designation": designation_map.get(employee_id)
                                }
                                node["children"].append(child_node)
                            return True
                        
                        if "children" in node:
                            for child in node["children"]:
                                if find_manager_and_add_child(child, manager_id, employee_id):
                                    return True
                        return False
                    
                    find_manager_and_add_child(result, manager_id, employee_id)
            
            return JsonResponse({"success": True, "org_structure": result}, status=200)
        
        except OrganizationDetails.DoesNotExist:
            return JsonResponse({"success": False, "status": 404, "message": "Organization not found."}, status=404)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "Internal server error.",
                "errors": str(e)
            }, status=500)



    

    
    @csrf_exempt
    def get_employee(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": "Missing user_id."
            }, status=400)
            
        user_instance = User.objects.get(id=user_id)
        organization = OrganizationDetails.objects.get(user_id=user_instance.id)
        employees = User.objects.filter(employeepersonaldetails__organization_id=organization.id,active = True)
        
        
        user_creations = UserCreation.objects.filter(employee_user_id__in=employees)
        
        user_serializer = HierarchyUserCreationSerializer(user_creations, many=True)
        
        return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "data":user_serializer.data
            })
        
    @csrf_exempt
    def update_hierarchy(self, request):
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({
                "success": False,
                "status": 400,
                "message": "Missing user_id."
            }, status=400)
        
        user_id = request.POST.get('user_id')
        user_instance = User.objects.get(id=user_id)
        # Assuming you have an instance of UserCreation
        user_creation_instance = UserCreation.objects.get(id=403)
        position = UserPosition.objects.create(user=user_creation_instance, x=1472, y=716.3079528808594)

        
        return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                # "data":user_serializer.data
            })
        
        
    @csrf_exempt
    def add_user_positions(self, request):
        try:

            user_id = request.POST.get('user_id')
            data_json = request.POST.get('data')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Missing user_id."
                }, status=400)

            if not data_json:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Missing data."
                }, status=400)

            try:
                data = json.loads(data_json)
            except json.JSONDecodeError:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid JSON."
                }, status=400)

            for item in data:
                user_creation_id = item.get('id')
                position = item.get('position')
                x = position.get('x')
                y = position.get('y')

                try:
                    user_creation = UserCreation.objects.get(id=user_creation_id)
                except UserCreation.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": 404,
                        "message": f"UserCreation object with id {user_creation_id} does not exist."
                    }, status=404)

                UserPosition.objects.update_or_create(
                    user=user_creation,
                    defaults={'x': x, 'y': y}
                )
            return JsonResponse({
                "success": True,
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": str(e)
            }, status=500)

