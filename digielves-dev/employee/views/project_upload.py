  
import random
from configuration import settings


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from digielves_setup.models import Board, Checklist, EmployeePersonalDetails, ProjectUpload, TaskHierarchy, TaskStatus, Tasks, User
from employee.seriallizers.task_seriallizers import TaskStatusSerializer
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage


from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.db import transaction
from django.core.exceptions import ValidationError
import pandas as pd
import os
import pytz
from django.db import transaction
from digielves_setup.helpers.error_trace import create_error_response
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from datetime import datetime, timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json


class UploadProjectViewSet(viewsets.ModelViewSet):

    # serializer_class = BoardCheckListTaskSerializer
    
    @csrf_exempt
    def upload_project(self, request):
        user_id = request.data.get('user_id')
        project_file = request.FILES.get('project_file')
        

        if not project_file:
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)

        # Check if the file extension is valid (.xlsx or .ods)
        valid_extensions = ['.xlsx', '.ods']
        file_extension = os.path.splitext(project_file.name)[1].lower()

        if file_extension not in valid_extensions:
            return JsonResponse({'error': 'Only Excel files (xlsx) and OpenDocument Spreadsheet files (ods) are supported.'}, status=400)

        # Read the data from the Excel or ODS file
        try:
            if file_extension == '.xlsx':
                excel_data = pd.read_excel(project_file, engine='openpyxl')
            elif file_extension == '.ods':
                excel_data = pd.read_excel(project_file, engine='odf')

            columns = list(excel_data.columns)

            included_fields = [
            'created_by', 'assign_to', 'task_topic', 'due_date', 'task_description', 
            'urgent_status', 'status', 'depend_on',
             'reopened_count',  
            'start_date', 'end_date','parent','id'
        ]

            # Get all field names of the Tasks model

            # Exclude the specified fields
            task_fields = [field.name for field in TaskHierarchy._meta.get_fields() if field.name in included_fields]
            
            print(user_id)
            get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

            task = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')

            status_serializer = TaskStatusSerializer(task, many=True)
            
            # Save the uploaded file to the ProjectUpload model
            ProjectUpload.objects.create(
                user_id=user_id,
                work_file_name=project_file.name,
                work_file=project_file
            )

            return JsonResponse({
                "success": True,
                "status": 200,
                "data": {
                    'columns': columns,
                    'task_fields': task_fields,
                    'status': status_serializer.data
                }
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
    




  


    @csrf_exempt
    def map_data(self, request):
        user_id = request.data.get('user_id')
        mapped_data = request.data.get('mapped_data', {})
        user_date_format = request.data.get('date_format', {})
        status_mapping = request.data.get('status', {})
        board_name = request.data.get('board_name')
        errors = []

        if not user_id:
            return JsonResponse({"error": "User ID is required."}, status=400)
        
        if not mapped_data:
            return JsonResponse({"error": "Mapped data is required."}, status=400)

        try:
            user_instance = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "Invalid User ID."}, status=400)

        
        
        try:
            with transaction.atomic():
                board = Board.objects.create(board_name=board_name, created_by=user_instance, favorite=None)
                checklist_mapping = {}
                
                if isinstance(status_mapping, str):
                    status_mapping = json.loads(status_mapping)
                    
                if isinstance(mapped_data, str):
                    mapped_data = json.loads(mapped_data)
                    
                    
                for status_key, status_value in status_mapping.items():
                    
                    checklist, created = Checklist.objects.get_or_create(board=board, name=status_value)
                    checklist_mapping[status_value] = checklist
                default_checklist, created = Checklist.objects.get_or_create(board=board, name='Default Name')
                IST = pytz.timezone('Asia/Kolkata')
                project_upload = ProjectUpload.objects.filter(user_id=user_id).last()
                if not project_upload:
                    return JsonResponse({"error": "No project upload found for this user."}, status=400)

                    
                try:
                    try:
                        excel_data = pd.read_excel(project_upload.work_file, engine='openpyxl')
                    except Exception:
                        excel_data = pd.read_excel(project_upload.work_file, engine='odf')
                except Exception as e:
                    return JsonResponse({"error": f"Error reading Excel file: {str(e)}"}, status=400)
                
                
                channel_layer = get_channel_layer()
                total_rows = len(excel_data)
                completed_rows = 0
                progress_group_name = f"task_progress_{user_id}"

                task_mapping = {}
                for index, row in excel_data.iterrows():
                    task_data = {}
                    created_by = user_instance  # Default creator
                    
                    created_by_email = row.get(next((key for key, value in mapped_data.items() if value == 'created_by'), None))
                    if created_by_email:
                        try:
                            try:
                                validate_email(created_by_email)
                            except Exception as e:
                                created_by = user_instance
                            creater = User.objects.filter(email=created_by_email).first()
                            if not creater:
                                created_by = user_instance
                            else:
                                created_by = creater
                        except DjangoValidationError:
                            errors.append(f"Invalid email provided for created_by: {created_by_email}")
                    

                    for column_name, task_field in mapped_data.items():
                        if column_name in excel_data.columns:
                            value = row[column_name]
                            if pd.isna(value):
                                continue
                            if task_field in ['due_date', 'start_date', 'end_date']:
                                try:
                                    value = convert_date_format(value, user_date_format)
                                except ValueError as e:
                                    errors.append(str(e))
                                    continue
                            task_data[task_field] = value

                    status_value = row.get(next((key for key, value in mapped_data.items() if value == 'status'), None))
                    if status_value:
                        try:
                            organization_id = EmployeePersonalDetails.objects.get(user_id=user_id).organization_id
                            if status_value in status_mapping:
                                status_instance = TaskStatus.objects.get(organization=organization_id, status_name=status_mapping[status_value])
                                task_data['status'] = status_instance
                                task_data['checklist'] = checklist_mapping[status_mapping[status_value]]
                            else:
                                errors.append("Invalid status.")
                        except EmployeePersonalDetails.DoesNotExist:
                            errors.append("Employee details not found.")
                    else:
                        task_data['checklist'] = default_checklist

                    assign_to_emails = row.get(next((key for key, value in mapped_data.items() if value == 'assign_to'), None))
                    assign_to_users = []
                    if assign_to_emails and not pd.isna(assign_to_emails):
                        emails = [email.strip() for email in assign_to_emails.split(',')]
                        for email in emails:
                            try:
                                validate_email(email)
                                user = User.objects.filter(email=email).first()
                                if user:
                                    assign_to_users.append(user)
                                else:
                                    errors.append(f"No user found with email: {email}")
                            except DjangoValidationError:
                                errors.append(f"Invalid email provided for assign_to: {email}")

                    task_data.pop('created_by', None)
                    task_data.pop('assign_to', None)
                    task_data.pop('depend_on', None)
                    task_data.pop('task_number', None)
                    task_data.pop('parent', None) 
                    # print(task_data)
                    task_number = row.get(next((key for key, value in mapped_data.items() if value == 'task_number'), None))
                    try:
                        task = TaskHierarchy.objects.create(
                            project_file_name=project_upload.work_file_name,
                            created_by=created_by,
                            **task_data
                        )
                        
                        if assign_to_users:
                            task.assign_to.set(assign_to_users)
                        
                        task_mapping[task_number] = task.id
                        
                        
                        completed_rows += 1
                        progress_percentage = (completed_rows / total_rows) * 100
                        progress_data = {
                            'total_rows': total_rows,
                            'row_count': completed_rows,
                            'progress': round(progress_percentage, 2)
                        }
                        async_to_sync(channel_layer.group_send)(
                            progress_group_name, 
                            {
                                "type": "send_task_progress",
                                "message": progress_data
                            }
                        )
                    

                    except ValidationError as e:
                        errors.append(str(e))
                        
                    
                    
                # After creating all tasks
                task_mapping = {}
                for index, row in excel_data.iterrows():
                    task_number = row.get(next((key for key, value in mapped_data.items() if value == 'task_number'), None))
                    task_topic = row.get(next((key for key, value in mapped_data.items() if value == 'task_topic'), None))
                    if task_number and task_topic:
                        task_instance = TaskHierarchy.objects.filter(task_topic=task_topic).last()
                        task_mapping[task_number] = task_instance.id

                    # Step 2: Set dependencies and parent relationships for each task
                for index, row in excel_data.iterrows():
                    task_number = row.get(next((key for key, value in mapped_data.items() if value == 'task_number'), None))
                    task_hierarchy_id = task_mapping.get(task_number)

                    if task_hierarchy_id:
                        task = TaskHierarchy.objects.filter(id=task_hierarchy_id).last()
                        
                        # Handling parent relationships
                        parent_task_number = row.get(next((key for key, value in mapped_data.items() if value == 'parent'), None))
                        if parent_task_number and not pd.isna(parent_task_number):
                            try:
                                parent_task_id = task_mapping.get(parent_task_number)
                                if parent_task_id and parent_task_id != task.id:
                                    task.parent = TaskHierarchy.objects.filter(id=parent_task_id).last()
                                    task.checklist = None
                                    task.save()
                                else:
                                    errors.append(f"Invalid parent task number for task number {task_number}: {parent_task_number}")
                                # Skip dependency handling if the task has a parent
                                continue
                            except Exception as e:
                                errors.append(f"Error setting parent for task number {task_number}: {str(e)}")

                        # Handling dependencies
                        depend_on_ids = row.get(next((key for key, value in mapped_data.items() if value == 'depend_on'), None))
                        depend_on_field_name = next((key for key, value in mapped_data.items() if value == 'depend_on'), None)
                        if depend_on_ids and not pd.isna(depend_on_ids):
                            depend_on_task_numbers = [int(float(id.strip())) for id in str(depend_on_ids).split(',') if id.strip()]
                            for depend_on_task_number in depend_on_task_numbers:
                                depend_on_task_id = task_mapping.get(depend_on_task_number)
                                if depend_on_task_id and depend_on_task_id != task.id:
                                    task.depend_on.add(depend_on_task_id)
                                else:
                                    errors.append(f"Invalid depend_on ID in column '{depend_on_field_name}' for task number {task_number}: {depend_on_task_number}")


                return JsonResponse({"success": True, "message": "Tasks created successfully.","board_id":board.id,  "errors": errors}, status=200)

        except Exception as e:
            return create_error_response(e, 500)






def convert_date_format(user_date, user_date_format=None, desired_format='%Y-%m-%d %H:%M:%S%z'):
    possible_formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',   # 2024-07-17T14:30:00.000Z
        '%Y-%m-%d %H:%M:%S',        # 2024-07-17 14:30:00
        '%m/%d/%Y %H:%M:%S',        # 07/17/2024 14:30:00
        '%d/%m/%Y %H:%M:%S',        # 17/07/2024 14:30:00
        '%d-%b-%Y %H:%M:%S',        # 17-Jul-2024 14:30:00
        '%Y-%m-%d %I:%M:%S %p',     # 2024-07-17 02:30:00 PM
    ]

    if isinstance(user_date, (int, float)):
        # If the input is Unix timestamp
        user_date = datetime.fromtimestamp(user_date, tz=timezone.utc)
    else:
        if isinstance(user_date, pd.Timestamp):
            user_date = user_date.strftime('%Y-%m-%d %H:%M:%S')

        for fmt in possible_formats:
            try:
                if fmt == '%s':
                    user_date = datetime.fromtimestamp(int(user_date), tz=timezone.utc)
                else:
                    user_date = datetime.strptime(user_date, fmt)
                    if user_date.tzinfo is None:
                        user_date = user_date.replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue
        else:
            raise ValueError("No valid date format found for the input date")

    formatted_date = user_date.strftime(desired_format)
    return formatted_date
