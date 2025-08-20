from django.http import JsonResponse
from configuration.gzipCompression import compress
from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import EmployeePersonalDetails, Notification, SaleStatusTrack, SalesAttachments, SalesFollowUp, SalesLead, SalesLeadSpecialAccess, SalesStatus, TaskStatus, User, UserFilters, notification_handler
from employee.seriallizers.sales_lead_seriallizers import CreateSalesLeadSerializer, GetSalesLeadSerializer, SalesFollowupSerializer, getSalesFollowupSerializer, salesStatusSerializer, updateSalesLeadSerializer

from rest_framework import status
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt

from django.core.serializers import serialize
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
import pandas as pd
from datetime import datetime
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import time
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class SalesLeadViewSet(viewsets.ModelViewSet):
    serializer_class = CreateSalesLeadSerializer

    

    @csrf_exempt
    def create_lead(self, request):
        print(request.data)
        serializer = CreateSalesLeadSerializer(data=request.data)

        try:
            if serializer.is_valid():
            
                
                user = User.objects.get(id = request.data['created_by'])
                get_org_id = EmployeePersonalDetails.objects.get(user_id=request.data['created_by'])
                assign_user_ids = request.data.get('assign_to', ',')
                assign_user_ids = [int(user_id) for user_id in assign_user_ids.split(',') if user_id.strip()]
                sales_lead_id=serializer.save()
                if assign_user_ids != [int(request.data.get('user_id'))]:
                    
                    try:
                        sales_status = SalesStatus.objects.filter(organization=get_org_id.organization_id, fixed_state="Assigned").order_by('order').first()
                    except Exception as e:
                        sales_status = SalesStatus.objects.filter(organization=get_org_id.organization_id).order_by('order').first()
                    sales = serializer.save(status=sales_status)
                    assign_users = User.objects.filter(id__in=assign_user_ids)
                    sales.assign_to.set(assign_users)
                    
                    try:
                        first_name = request.data.get('first_name', '')
                        last_name = request.data.get('last_name', '')
                        post_save.disconnect(notification_handler, sender=Notification)
                        notification = Notification.objects.create(
                            user_id=request.user,
                            where_to="sales",
                            notification_msg=f"You have been assigned new lead: {first_name} {last_name}",
                            action_content_type=ContentType.objects.get_for_model(SalesLead),
                            action_id=sales_lead_id.id
                        )
                        
                        notification.notification_to.set(assign_users)  
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                       
                        
                    except Exception as e:
                        print("Notification creation failed:", e)
                    

                else:
                    
                    try:
                        sales_status = SalesStatus.objects.filter(organization=get_org_id.organization_id, fixed_state="Identifier").order_by('order').first()
                    except Exception as e:
                        sales_status = SalesStatus.objects.filter(organization=get_org_id.organization_id).order_by('order').first()
                    sales = serializer.save(status=sales_status)
         
                
                
                SaleStatusTrack.objects.create(changed_by=user,sales_lead=sales_lead_id, to_status=sales_status)

                attachments = request.FILES.getlist('attachments') 
        

                for attachment in attachments:
                    
                    try:

                       
                        sale_attachment = SalesAttachments.objects.create(sales_lead=sales_lead_id, attachment=attachment)
                    except Exception as e:
                        return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to add attachment",
                    "errors": str(e)
                })
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Lead created successfully.",
                    "data": {
                        "sales": serializer.data
                        
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Lead.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def update_lead(self, request):
        try:
            lead_id = request.data.get('lead_id')
            if lead_id:
                obj = SalesLead.objects.get(id=lead_id)
                serializer = updateSalesLeadSerializer(obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Sales Lead updated successfully",
                    })
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "error": serializer.errors
                    })
            
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Missing 'lead_id' parameter",
                "data": {}
            })
    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Sales Lead not found",
                "data": {},
                "error": str(e)
            })
    
    @csrf_exempt
    def getSalesLead(self, request):

        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })

        userr = User.objects.get(id=user_id)
        sales_created_by = SalesLead.objects.filter(
            created_by=user_id,inTrash=False).order_by('lead_created_date')
        sales_assigned_to = SalesLead.objects.filter(
            assign_to=user_id, inTrash=False).order_by('lead_created_date')


        all_sales = set()

        # Add sales IDs to the set
        for sales in sales_created_by:
            all_sales.add(f"t_{sales.id}")
        for sales in sales_assigned_to:
            all_sales.add(f"t_{sales.id}")
            
        get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
        task_statuses = SalesStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "sales": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


        
        for sales_id in all_sales:
            sales_num = int(sales_id.split("_")[1])
            sale = SalesLead.objects.get(id=sales_num)
            

                
            
            created_by_data = serialize('json', [sale.created_by])
            created_by_data = created_by_data[1:-1]
            created_by_data = {
                "id": sale.created_by.id,
                "email": sale.created_by.email,
                "firstname": sale.created_by.firstname,
                "lastname": sale.created_by.lastname,
            }
            
            assign_to_data = []
            sale1 = sale.assign_to.all()
            for user in sale1:
                assign_to_data.append({
                    "id": user.id,
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                })
                
    
            
            sales_data = {
                "id": sales_id,
                "title": f"{sale.first_name} {sale.last_name}",
                "email": sale.email,
                "phone_number": sale.phone_number,
                "address": sale.address,
                "description": sale.notes,
                "lead_created_date": sale.lead_created_date.isoformat(),
                "company_name":sale.company_name,
                "designation":sale.designation,
                "lead_source":sale.lead_source,
                "reference_source":sale.reference_source,
                'annual_income':sale.annual_income,
                'budget': sale.budget,
                "followup_date": sale.next_followup_date.isoformat() if sale.next_followup_date else None,
                "assign_to": assign_to_data,
                # "urgent_status": sale.urgent_status,
                "status": sale.status,
                "created_at": sale.created_at.isoformat(),
                "created_by": created_by_data,
                
            }
            
            
            

            for idx, (title,fix_state, order,status_id) in enumerate(fixed_state_titles_and_ids):
                if sale.status and sale.status.id == status_id:
                    status_info = {
                        "id": sale.status.id,
                        "status_name": sale.status.status_name,
                        "color": sale.status.color,
                    }
                    sales_data["status"] = status_info
                    data[idx]["sales"].append(sales_data)
                    break
        
        users_with_access = SalesLeadSpecialAccess.objects.filter(access_to=userr).select_related('user')
        users_with_access_gave = SalesLeadSpecialAccess.objects.filter(user=userr).select_related('access_to')

        access_list = [
            {
                'user_id': access.user.id,
                'user_email': access.user.email,
                'access_type': access.access_type
            } for access in users_with_access
        ]

        access_list_gave = [
            {
                'user_id': access.access_to.id,
                'user_email': access.access_to.email,
                'access_type': access.access_type
            } for access in users_with_access_gave
        ]

        try:
            board_view = UserFilters.objects.get(user=user_id).sales_board_view
        except UserFilters.DoesNotExist:
            board_view = None

        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User sales retrieved successfully.",
            "access": access_list,
            "access_to": access_list_gave,
            "data": data,  # Ensure 'data' is defined or retrieved somewhere in your code
            "board_view": board_view
        }

        return JsonResponse(response, encoder=DjangoJSONEncoder)
    
    
    
    @csrf_exempt
    def changeNextFollowupDate(self, request):
        try:
            sales_id = request.data.get('sales_id')
            
            user_id = request.data.get('user_id')
            follow_up_date = request.data.get('next_followup_date')
            user_instance = User.objects.get(id=user_id)
             
            try:
                
                sales = SalesLead.objects.filter(Q(created_by=user_id) | Q(assign_to=user_id), id=sales_id).distinct().first()
                
                sales.next_followup_date=follow_up_date
                sales.save()
                
                response={
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Sales status updated successfully.",
               }

                return JsonResponse(response)
            
            except SalesLead.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 403,
                    "message": "You don't have permission to update this Sales",
                })
                
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Sales status.",
                "errors": str(e)
            })
    
    @csrf_exempt
    def changeIndividualLeadStatus(self, request):
        try:
            sales_id = request.data.get('sales_id')
            
            user_id = request.data.get('user_id')
            user_instance = User.objects.get(id=user_id)
             
            try:
                
                sales = SalesLead.objects.filter(Q(created_by=user_id) | Q(assign_to=user_id), id=sales_id).distinct().first()
                 
                Status = request.data.get('status')
                if Status:
                    got_task_statu = SalesStatus.objects.get(id=Status)
                    try:
                        status_track = SaleStatusTrack.objects.get(to_status = sales.status.id, sales_lead = sales.id)
                    
                        SaleStatusTrack.objects.create(changed_by=user_instance,sales_lead=sales,from_status=  sales.status,to_status=got_task_statu, from_status_date=status_track.status_change_date)
                    except Exception as e:
                        try:
                            SaleStatusTrack.objects.create(changed_by=user_instance,sales_lead=sales,from_status=  sales.status,to_status=got_task_statu)
                        except:
                            pass
                    sales.status =got_task_statu
                    try:    
                        post_save.disconnect(notification_handler, sender=Notification)
                        notification = Notification.objects.create(
                            user_id=request.user,
                            where_to="sales",
                            notification_msg=f"Lead '{sales.first_name} {sales.last_name}' Status has been updated to {got_task_statu.status_name}",
                            action_content_type=ContentType.objects.get_for_model(SalesLead),
                            action_id=sales.id
                        )
                        
        
                        if str(user_id) == str(sales.created_by.id):                    
                            notification.notification_to.set(sales.assign_to.all())
                        else:
                            notification.notification_to.add(sales.created_by)
                            
                            # Exclude user_id from task.assign_to.all() if user_id is present in assign_to
                            assigned_users = sales.assign_to.exclude(id=user_id).all()
                            notification.notification_to.add(*assigned_users)
                            
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                    except Exception as e:
                        pass
                    
                due_date = request.data.get('due_date')
                if due_date is not None:
                    sales.due_date = due_date
                    
                    
                    try:    
                        post_save.disconnect(notification_handler, sender=Notification)
                        notification = Notification.objects.create(
                            user_id=request.user,
                            where_to="sales",
                            notification_msg=f"Lead '{sales.first_name} {sales.last_name}' Due Date has been changed",
                            action_content_type=ContentType.objects.get_for_model(SalesLead),
                            action_id=sales.id
                        )
                        
        
                        if str(user_id) == str(sales.created_by.id):                    
                            notification.notification_to.set(sales.assign_to.all())
                        else:
                            notification.notification_to.add(sales.created_by)
                            
                            # Exclude user_id from task.assign_to.all() if user_id is present in assign_to
                            assigned_users = sales.assign_to.exclude(id=user_id).all()
                            notification.notification_to.add(*assigned_users)
                            
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                    except Exception as e:
                        pass
                    
                    
                    

                assign_user_ids = request.data.get('assign_to', ',')
                assign_user_ids = [int(user_id) for user_id in assign_user_ids.split(',') if user_id.strip()]
                
                if assign_user_ids is not None and assign_user_ids:
                    assign_users = User.objects.filter(id__in=assign_user_ids)
                    
                    try:    
                        post_save.disconnect(notification_handler, sender=Notification)
                        
                        # Get currently assigned users
                        current_assigned_users = set(sales.assign_to.all())

                        # Determine new users to notify
                        new_users_to_notify = [user for user in assign_users if user not in current_assigned_users]

                        notification = Notification.objects.create(
                            user_id=user_instance,
                            where_to="sales",
                            notification_msg=f"You have been assigned a Lead: {sales.first_name} {sales.last_name}",
                            action_content_type=ContentType.objects.get_for_model(SalesLead),
                            action_id=sales.id
                            
                        )
                        

                        notification.notification_to.set(new_users_to_notify)
                            
                            
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                    except Exception as e:
                        print("-------------error",str(e))
                        pass
                    
                    
                    sales.assign_to.set(assign_users)
                    
                sales.save()
                
                
            except SalesLead.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 403,
                    "message": "You don't have permission to update this Sales",
                })
            
            
            response={
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Sales status updated successfully.",
               }

            return JsonResponse(response)

        except SalesLead.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Sales not found.",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Sales status.",
                "errors": str(e)
            })
            
    
    @csrf_exempt
    def getSpecificSalesLeadDetails(self, request):
        user_id = request.GET.get('user_id')
        sales_id = request.GET.get('sales_id')

        if not user_id or not sales_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. Both user_id and sales_id are required."
            })

        try:
            # Get the specific SalesLead object
            sales_lead = SalesLead.objects.get(id=sales_id, inTrash=False)
        except SalesLead.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "SalesLead not found."
            })

        # Serialize the SalesLead object
        seriallized_data = GetSalesLeadSerializer(sales_lead)

        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "SalesLead retrieved successfully.",
            "data": seriallized_data.data,
        }

        return compress(response)
    
    
    @csrf_exempt
    def delete_lead(self, request):
        user_id = request.GET.get('user_id')
        sales_id = request.GET.get('sales_id')

        if not user_id or not sales_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. Both user_id and sales_id are required."
            })

        try:
            # Get the specific SalesLead object
            sales_lead = SalesLead.objects.get(id=sales_id, inTrash=False)
        except SalesLead.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "SalesLead not found."
            })

        sales_lead.inTrash=True
        sales_lead.save()
        # Serialize the SalesLead object

        response = {
            "success": True,
        }

        return JsonResponse(response)
    
    @csrf_exempt
    def delete_sales_leads_by_user(self,request):
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "user_id is required."
                }, status=400)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": 404,
                    "message": "User not found."
                }, status=404)
            
            sales_leads_deleted, _ = SalesLead.objects.filter(created_by=user).delete()
            
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": f"Deleted {sales_leads_deleted} sales leads created by user {user_id}."
            }, status=200)



class SalesStatusViewSet(viewsets.ModelViewSet):


    

    @csrf_exempt
    def get_sales_status(self, request):
        try:
            user_id = request.GET.get('user_id')
            get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

            sales = SalesStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')

            status_serializer = salesStatusSerializer(sales, many=True)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User Sales status retrieved successfully.",
                "data": status_serializer.data
            }

            return JsonResponse(response)

        except EmployeePersonalDetails.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "EmployeePersonalDetails not found for the specified user.",
                "data": {}
            }
            return JsonResponse(response)

        except TaskStatus.DoesNotExist:
            response = {
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "SalesStatus not found for the specified organization.",
                "data": {}
            }
            return JsonResponse(response)

        except Exception as e:
            response = {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An error occurred: {str(e)}",
                "data": {}
            }
            return JsonResponse(response)


class SalesExportAndImportViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def ImportExcel(self, request):
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        file = request.FILES.get('file')

        if not user_id or not file:
            return JsonResponse({
                "error": "Invalid request. user_id or file is missing.",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
            total_rows = len(df)
            success_count = 0
            channel_layer = get_channel_layer()
            progress_group_name = f"progress_{user_id}"

            for index, row in df.iterrows():
                lead_name = row['Lead Name'].strip() if isinstance(row['Lead Name'], str) else None
                if not lead_name:
                    continue
                try:
                    get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
                    try:
                        task_statuses = SalesStatus.objects.filter(organization=get_org_id.organization_id, status_name=row['Status']).order_by('order', 'created_at').first()
                        if not task_statuses:
                            raise SalesStatus.DoesNotExist
                    except SalesStatus.DoesNotExist:
                        task_statuses = SalesStatus.objects.filter(organization=get_org_id.organization_id, fixed_state="Identifier").order_by('order', 'created_at').first()
                    except:
                        task_statuses = SalesStatus.objects.filter(organization=get_org_id.organization_id, fixed_state="Identifier").order_by('order', 'created_at').first()
                    lead_name_parts = lead_name.split()
                    if len(lead_name_parts) > 0:
                        first_name = lead_name_parts[0]
                        last_name = ' '.join(lead_name_parts[1:])
                    else:
                        first_name = None
                        last_name = None
                    lead_data = {
                        'created_by_id': user_id,
                        'lead_source': row['Lead Source'].strip() if row.get('Lead Source') and isinstance(row['Lead Source'], str) else None,
                        'reference_source': row['Reference Source'].strip() if row.get('Reference Source') and  isinstance(row['Reference Source'], str) else None,
                        'lead_created_date': pd.to_datetime(row['Lead Created date']).to_pydatetime() if row.get('Lead Created date') and row['Lead Created date'] else timezone.now(),
                        'first_name': first_name,
                        'last_name': last_name.strip() if isinstance(last_name, str) else None,
                        'email': row['Email'].strip() if row.get('Email') and isinstance(row['Email'], str) else None,
                        'phone_number': row['Phone No.'].strip() if row.get('Phone No.') and isinstance(row['Phone No.'], str) else None,
                        'address': row['Address'].strip() if row.get('Address') and isinstance(row['Address'], str) else None,
                        'company_name': row['Company Name'].strip() if  row.get('Company Name') and isinstance(row['Company Name'], str) else None,
                        'designation': row['Designation'].strip() if row.get('Designation') and isinstance(row['Designation'], str) else None,
                        'budget': row['Budget'].strip() if row.get('Budget') and isinstance(row['Budget'], str) else None,
                        'annual_income': row['Annual Expected Revenue'].strip() if row.get('Annual Expected Revenue') and isinstance(row['Annual Expected Revenue'], str) else None,
                        'status': task_statuses,
                        'notes': row['notes'].strip() if row.get('notes') and isinstance(row['notes'], str) else None,
                    }

                    with transaction.atomic():
                        lead = SalesLead.objects.create(**lead_data)

                        SaleStatusTrack.objects.create(
                            changed_by=user,
                            sales_lead=lead,
                            to_status=task_statuses
                        )

                        try:
                            if isinstance(row['assign_to'], str):
                                assign_to_ids = row['assign_to'].strip().split(',')
                                for user_id in assign_to_ids:
                                    user = User.objects.get(email=user_id.strip())
                                    lead.assign_to.add(user)
                        except Exception as e:
                            pass
                            

                    success_count += 1
                    
                    
                    progress = (index + 1) / total_rows * 100
                    message = {
                        'progress': progress,
                        'row_count': index + 1,
                        'total_rows': total_rows,
                    }
                    async_to_sync(channel_layer.group_send)(
                        progress_group_name,
                        {
                            'type': 'send_progress',
                            'message': message
                        }
                    )
            

                except ObjectDoesNotExist as e:
                    return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse(
                {
                    'success':True,
                    'status': f'Successfully imported {success_count} leads.'
                 }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return create_error_response(e, status.HTTP_500_INTERNAL_SERVER_ERROR)




class SalesSpecialAccessViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def give_access(self, request):
        try:
            user_id = request.POST.get('user_id')
            access_to = request.POST.get('access_to')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is required."
                })

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found."
                })

            if access_to is None or access_to.strip() == "":
                # If access_to is not provided or is empty, delete all existing access
                SalesLeadSpecialAccess.objects.filter(user=user).delete()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "All existing access removed successfully."
                })

            # Ensure access_to contains valid IDs
            access_to_ids = [id.strip() for id in access_to.split(',') if id.strip().isdigit()]
            if not access_to_ids:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid access_to IDs provided."
                })

            access_to_ids = [int(id) for id in access_to_ids]

            existing_access = SalesLeadSpecialAccess.objects.filter(user=user)

            # Remove access that is not in the new list
            existing_access.exclude(access_to__id__in=access_to_ids).delete()

            for access_to_id in access_to_ids:
                try:
                    user_access = User.objects.get(id=access_to_id)
                    SalesLeadSpecialAccess.objects.get_or_create(user=user, access_to=user_access)
                except User.DoesNotExist:
                    continue  # Skip if the user does not exist

            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Access granted successfully."
            }

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "errors": str(e)
            })
    @csrf_exempt
    def get_leads_of_accessed_user(self, request):
        
        user_id = request.GET.get('user_id')
        access_user_id = request.GET.get('access_user_id')

        if not user_id:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid request. user_id is missing."
            })

        userr = User.objects.get(id=user_id)
        access_user = User.objects.get(id=access_user_id)
        
        sales_created_by = SalesLead.objects.filter(
            created_by=access_user_id,inTrash=False).order_by('lead_created_date')
        sales_assigned_to = SalesLead.objects.filter(
            assign_to=access_user_id, inTrash=False).order_by('lead_created_date')


        all_sales = set()

        # Add sales IDs to the set
        for sales in sales_created_by:
            all_sales.add(f"t_{sales.id}")
        for sales in sales_assigned_to:
            all_sales.add(f"t_{sales.id}")
            
        get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
        task_statuses = SalesStatus.objects.filter(organization=get_org_id.organization_id).order_by('order', 'created_at')

        fixed_state_titles_and_ids = [(Status.status_name,Status.fixed_state,Status.order ,Status.id) for Status in task_statuses]

        data = [
            {"id": f"s_{status_id}", "title": title,"fixed_state":fix_state,"order": order, "status_id": status_id, "sales": []}
            for idx, (title,fix_state, order ,status_id) in enumerate(fixed_state_titles_and_ids)
        ]


        
        for sales_id in all_sales:
            sales_num = int(sales_id.split("_")[1])
            sale = SalesLead.objects.get(id=sales_num)
            

                
            
            created_by_data = serialize('json', [sale.created_by])
            created_by_data = created_by_data[1:-1]
            created_by_data = {
                "id": sale.created_by.id,
                "email": sale.created_by.email,
                "firstname": sale.created_by.firstname,
                "lastname": sale.created_by.lastname,
            }
            
            assign_to_data = []
            sale1 = sale.assign_to.all()
            for user in sale1:
                assign_to_data.append({
                    "id": user.id,
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                })
            
            sales_data = {
                "id": sales_id,
                "title": f"{sale.first_name} {sale.last_name}",
                "description": sale.notes,
                "email": sale.email,
                "phone_number": sale.phone_number,
                "lead_created_date": sale.lead_created_date.isoformat(),
                "company_name":sale.company_name,
                "designation":sale.designation,
                "lead_source":sale.lead_source,
                "reference_source":sale.reference_source,
                "assign_to": assign_to_data, 
                "next_followup_date": sale.next_followup_date.isoformat() if sale.next_followup_date else None,
                # "urgent_status": sale.urgent_status,
                "status": sale.status,
                "created_at": sale.created_at.isoformat(),
                "created_by": created_by_data,
                
            }
            
            
            

            for idx, (title,fix_state, order,status_id) in enumerate(fixed_state_titles_and_ids):
                if sale.status and sale.status.id == status_id:
                    status_info = {
                        "id": sale.status.id,
                        "status_name": sale.status.status_name,
                        "color": sale.status.color,
                    }
                    sales_data["status"] = status_info
                    data[idx]["sales"].append(sales_data)
                    break
        
        users_with_access = SalesLeadSpecialAccess.objects.filter(access_to = userr)
        # Formatting the list of users with access
        access_list = []
        for access in users_with_access:
            access_list.append({
                'user_id': access.user.id,
                'user_email': access.user.email,
                'access_type': access.access_type
            })
        try:
            board_view = UserFilters.objects.get(user=user_id).sales_board_view
        except Exception as e:
            board_view = None    
        response = {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User sales retrieved successfully.",
            "access_board":True,
            "access":access_list,
            "data": data,
            "board_view" : board_view
        }

        return compress(response)
    
    
class SalesFollowupViewSet(viewsets.ModelViewSet):
    
    
    @csrf_exempt
    def create_note(self, request):
        note = request.data.get('note')
        user_id = request.data.get('user_id')
        id = request.data.get('id')
        try:
            mom=SalesFollowUp.objects.get(id=id)
            mom.notes=note
            mom.save()
            return JsonResponse({
                 "success": True,
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create Sales note.",
                "errors": str(e)
            })
        
        
    @csrf_exempt
    def create_sales_followup(self, request):
        print(request.data)
        serializer = SalesFollowupSerializer(data=request.data)

        try:
            if serializer.is_valid():
                serializer = serializer.save()
                response_serializer = SalesFollowupSerializer(serializer)
                
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Sales Follow-up created successfully.",
                    "data": {
                        "follow_up": response_serializer.data
                        
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Lead.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create Sales Follow-up.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def get_sales_lead_followup(self, request):
        try:
            lead = request.GET.get('sales_lead_id')
            obj = SalesFollowUp.objects.filter(sales_lead=lead).order_by('followup_date')
            
            serializer = getSalesFollowupSerializer(obj, many=True)
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Sales Follow-up created successfully.",
                "data": {
                    "followup": serializer.data
                    
                }
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create Sales Follow-up.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def create_notes(self, request):
        print(request.data)
        try:
            if serializer.is_valid():
                serializer = serializer.save()
                response_serializer = SalesFollowupSerializer(serializer)
                
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Sales Follow-up created successfully.",
                    "data": {
                        "follow_up": response_serializer.data
                        
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Lead.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to create Sales Follow-up.",
                "errors": str(e)
            })
            
    
        
 