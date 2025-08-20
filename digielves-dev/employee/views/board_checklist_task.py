  
import random
from configuration import settings
from digielves_setup.models import Board, Checklist, TaskAttachments, Tasks, User, Notification, Redirect_to, notification_handler
from employee.seriallizers.board_seriallizer import BoardCheckListSerializer, BoardCheckListTaskSerializer, BoardSerializer

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from employee.seriallizers.user_serillizer import UserSerializer
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from decimal import Decimal
from datetime import datetime
from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
class BoardCheckListTaskViewSet(viewsets.ModelViewSet):

    serializer_class = BoardCheckListTaskSerializer
    
    @csrf_exempt
    def AddBoardCheckListTask(self,request):
        print(request.data)
        serializer = BoardCheckListTaskSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Checklist Task created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Task.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })



    def calculate_remaining_weekdays(self, from_date, to_date, included_weekdays):
        current_date = from_date
        remaining_weekdays = []

        while current_date <= to_date:
            if current_date.weekday() in included_weekdays:
                remaining_weekdays.append(str(current_date))
            current_date += timedelta(days=1)

        return remaining_weekdays

    @csrf_exempt
    def create_task(self, request):
        print(request.data)
        
        user_id = request.data.get('user_id')
        due_date = request.data.get('due_date')
        task_topic = request.data.get('task_topic')
        if not user_id:
            return JsonResponse({
                "success": False,
                "message": "Invalid request. user_id is missing."
            })
        if not due_date:
            return JsonResponse({
                "success": False,
                "message": "Invalid request. due_date is missing."
            })

        if not task_topic:
            return JsonResponse({
                "success": False,
                "message": "Invalid request. task_topic is missing."
            })
        
        serializer = BoardCheckListTaskSerializer(data=request.data)
        if serializer.is_valid():

            serializer_data = serializer.validated_data


            with transaction.atomic():
                try:
                # If the checklist_id is provided, generate sequence based on checklist, otherwise set it to "1"
                    checklist_id = request.data.get('checklist')
                    board_id = None
                    checklist = None
                    if checklist_id:
                        try:
                            checklist = Checklist.objects.get(id=checklist_id)
                        
                            print(checklist.board.id)
                            board_id = checklist.board.id
                        except Checklist.DoesNotExist:
                            return JsonResponse({
                                "success": False,
                                "status": status.HTTP_404_NOT_FOUND,
                                "message": "Checklist not found.",
                            })

                    if checklist_id and checklist:
                        max_sequence = Tasks.objects.filter(checklist_id=checklist_id).aggregate(Max('sequence'))['sequence__max']
                        if max_sequence is not None:
                            max_sequence = Decimal(max_sequence)
                            sequence = str(int(max_sequence) + 1)
                        else:
                            sequence = "5"
                    else:
                        sequence = "1"

                    # Common attributes for both cases
                    common_attributes = {
                        "created_by": serializer_data.get("created_by"),
                        "checklist": serializer_data.get("checklist"),
                        "task_topic": serializer_data.get("task_topic"),
                        "task_description": serializer_data.get("task_description"),
                        "urgent_status": serializer_data.get("urgent_status", False),
                        "completed": serializer_data.get("completed", False),
                        "sequence": sequence,
                        "is_personal": serializer_data.get("is_personal", False),
                    }
                    assign_to_ids_string = request.data.get('assign_to', '')
                    assign_user_ids = [int(id) for id in assign_to_ids_string.split(',') if id.isdigit()]
                
                    repeat_task = request.data.get('repeat_task', False)
                
                    if repeat_task==True or repeat_task=="true":
                        
                        from_due_date_str = request.data.get('from_due_date')
                        to_due_date_str = request.data.get('to_due_date')
                        to_due_time_str = request.data.get('to_time_date')
                        
                        included_weekdays_str = request.data.get('included_weekdays', '')

                        # Convert due dates to date objects
                        from_due_date = datetime.strptime(from_due_date_str, '%Y-%m-%d').date()
                        to_due_date = datetime.strptime(to_due_date_str, '%Y-%m-%d').date()
                        
                        included_weekdays = [int(day) for day in included_weekdays_str.split(',') if day]
                        # Create tasks for the date range and included weekdays
                        remaining_dates = self.calculate_remaining_weekdays(from_due_date, to_due_date, included_weekdays)
                        
                        for remaining_date_str in remaining_dates:
                            remaining_date = datetime.strptime(remaining_date_str, '%Y-%m-%d').date()
                            due_datetime_str = f"{remaining_date}T{to_due_time_str}"
                            # parsed_datetime = datetime.strptime(due_datetime_str, '%Y-%m-%d'+'T'+'%H:%M:%S')
                            # utc_datetime = timezone.make_aware(parsed_datetime, timezone=timezone.utc)
                            common_attributes["due_date"] = due_datetime_str
                            new_task = Tasks.objects.create(**common_attributes)
                            
                            new_task.assign_to.set(assign_user_ids)
                            
                            new_task.save()
                            attachments = request.FILES.getlist('attachments')
                            user_folder = settings.MEDIA_ROOT
                            # task_attachments = []
                            for attachment in attachments:
                                try:
                                    file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
                                    file_path = '/employee/task_attachment/' + file_name
                                    with open(user_folder + file_path, 'wb') as f:
                                        f.write(attachment.read())

                                    task_attachment = TaskAttachments.objects.create(task=new_task, attachment=file_path)
                                    # task_attachments.append(task_attachment)
                                except Exception as e:
                                    return JsonResponse({
                                        "success": False,
                                        "status": status.HTTP_400_BAD_REQUEST,
                                        "message": "Failed to create Task.",
                                        "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
                                    })
                    else:

                        try:
                            due_date_date = request.data.get('due_date')

                            # # Remove the timezone information from the input date string
                            # due_date_date = due_date_date.split(' GMT')[0]
                            # parsed_date = datetime.strptime(due_date_date, '%a %b %d %Y %H:%M:%S')

                            # utc_date = timezone.make_aware(parsed_date, timezone=timezone.utc)
                        
                            common_attributes["due_date"] = due_date_date
                         
                            task = serializer.save(**common_attributes)
                        except Exception as e:
                                
                                return JsonResponse({
                                    "success": False,
                                    "status": status.HTTP_400_BAD_REQUEST,
                                    "message": "Exception when assigning user",
                                    "errors": str(e),
                                })

                        # Notification and attachments code...
                        
                        

                        if assign_user_ids:
                        
                            try:
                                
                                assign_users = User.objects.filter(id__in=assign_user_ids)
                        
                                if serializer_data.get("created_by") not in assign_users:
                                

                                    task.assign_to.set(assign_users)
                                else:
                                    pass
                            except Exception as e:
                                
                                return JsonResponse({
                                    "success": False,
                                    "status": status.HTTP_400_BAD_REQUEST,
                                    "message": "Exception when assigning user",
                                    "errors": str(e),
                                })
                            try:
                                if serializer_data.get("created_by") not in assign_users:
                                    post_save.disconnect(notification_handler, sender=Notification)
                                    notification = Notification.objects.create(
                                        user_id=request.user,
                                        where_to="customboard" if checklist_id else "myboard",
                                        notification_msg=f"You have been assigned a task: {task.task_topic}",
                                        action_content_type=ContentType.objects.get_for_model(Tasks),
                                        action_id=task.id,
                                        other_id=board_id
                                    )

                                    notification.notification_to.set(assign_users)
                                    
                                    post_save.connect(notification_handler, sender=Notification)
                                    post_save.send(sender=Notification, instance=notification, created=True)

                                else:
                                    pass
                            except Exception as e:
                                print("------------------------exception: %s" % e)
                                pass

                        attachments = request.FILES.getlist('attachments')
                        user_folder = settings.MEDIA_ROOT
                        task_attachments = []
                        for attachment in attachments:
                            try:
                                file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
                                file_path = '/employee/task_attachment/' + file_name
                                with open(user_folder + file_path, 'wb') as f:
                                    f.write(attachment.read())

                                task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
                                task_attachments.append(task_attachment)
                            except Exception as e:
                                return JsonResponse({
                                    "success": False,
                                    "status": status.HTTP_400_BAD_REQUEST,
                                    "message": "Failed to create Task.",
                                    "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
                                })

                # Return the response...
                # task_data = serializer.data
                # task_data["assign_to"] = assign_user_ids
                # task_data["attachments"] = [attachment.attachment for attachment in task_attachments]
                except ValidationError as ve:
                    # Handle validation errors
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Validation error.",
                        "errors": str(ve),
                    })
                except ValueError as ve:
                    # Handle value error
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_422_UNPROCESSABLE_ENTITY, 
                        "message": "Your administrator has not added a status for tasks yet. Please contact your administrator to set up task statuses.",
                        "error":str(ve)
                    })
                except Exception as e:
                    # Handle value error
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_422_UNPROCESSABLE_ENTITY, 
                        "message": e,
                    })
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Task created successfully.",
                "data": {
                        "task_id": task.id,
                        "board_id": task.checklist.board.id if task.checklist else None
                        }
                })
        else:
            return JsonResponse({
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "errors": serializer.errors
        })


        

    @csrf_exempt
    def getRemainingUsers(self, request):
        try:
            board_id = request.GET.get('board_id')
            task_id = request.GET.get('task_id')

            if not board_id or not task_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. Both board_id and task_id are required."
                })

            try:
                board = Board.objects.get(id=board_id)
            except Board.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Board not found.",
                })

            try:
                task = Tasks.objects.get(id=task_id)
            except Tasks.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Task not found.",
                })

           
            assigned_users = task.assign_to.all()

            
            board_users = board.assign_to.all()

            
            remaining_users = [user for user in board_users if user not in assigned_users]

            
            serializer = UserSerializer(remaining_users, many=True)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Remaining users retrieved successfully.",
                "data": serializer.data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve remaining users.",
                "errors": str(e)
            })

    # @csrf_exempt
    # def create_task(self, request):
    #     serializer = BoardCheckListTaskSerializer(data=request.data)

    #     try:
    #         if serializer.is_valid():
    #             checklist_id = request.data.get('checklist')  # Assuming you have the checklist ID in the request data
    #             if not checklist_id:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_400_BAD_REQUEST,
    #                     "message": "Invalid request. checklist_id is missing."
    #                 })

                
    #             max_sequence = Tasks.objects.filter(checklist_id=checklist_id).aggregate(Max('sequence'))['sequence__max']
    #             if max_sequence is not None:
    #                 max_sequence = Decimal(max_sequence)
    #                 sequence = str(int(max_sequence) + 1)
    #             else:
    #                 sequence = "1"

    #             task = serializer.save(sequence=sequence)  

    #             assign_user_ids = request.data.get('assign_to', [])
    #             if assign_user_ids:
    #                 assign_users = User.objects.filter(id__in=assign_user_ids)
    #                 task.assign_to.set(assign_users)

    #             attachments = request.FILES.getlist('attachments')
    #             user_folder = settings.MEDIA_ROOT
    #             task_attachments = []
    #             for attachment in attachments:
    #                 try:
    #                     file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
    #                     file_path = '/employee/task_attachment/' + file_name
    #                     with open(user_folder + file_path, 'wb') as f:
    #                         f.write(attachment.read())

    #                     task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
    #                     task_attachments.append(task_attachment)
    #                 except Exception as e:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": status.HTTP_400_BAD_REQUEST,
    #                         "message": "Failed to create Task.",
    #                         "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
    #                     })

    #             serializer.save()

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_201_CREATED,
    #                 "message": "Task created successfully.",
    #                 "data": {
    #                     "task": serializer.data,
    #                     "attachments": [attachment.attachment for attachment in task_attachments]
    #                 }
    #             })
    #         else:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to create Task.",
    #                 "errors": serializer.errors
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })
    # @csrf_exempt
    # def create_task(self, request):
    #     serializer = BoardCheckListTaskSerializer(data=request.data)

    #     try:
    #         if serializer.is_valid():
    #             checklist_id = request.data.get('checklist_id')
    #             if checklist_id:
    #                 try:
    #                     checklist = Checklist.objects.get(id=checklist_id)
    #                 except Checklist.DoesNotExist:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": status.HTTP_404_NOT_FOUND,
    #                         "message": "Checklist not found.",
    #                     })
    #                 max_sequence = Tasks.objects.filter(checklist_id=checklist_id).aggregate(Max('sequence'))['sequence__max']
    #                 if max_sequence is not None:
    #                     max_sequence = Decimal(max_sequence)
    #                     sequence = str(int(max_sequence) + 1)
    #                 else:
    #                     sequence = "1"

    #                 task = serializer.save(sequence=sequence)  

                

    #             if checklist_id:
    #                 task.checklist = checklist
    #                 task.save()

    #             assign_user_ids = request.data.get('assign_to', [])
    #             if assign_user_ids:
    #                 assign_users = User.objects.filter(id__in=assign_user_ids)
    #                 task.assign_to.set(assign_users)

    #             attachments = request.FILES.getlist('attachments')
    #             user_folder = settings.MEDIA_ROOT
    #             task_attachments = []
    #             for attachment in attachments:
    #                 try:
    #                     file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
    #                     file_path = '/employee/task_attachment/' + file_name
    #                     with open(user_folder + file_path, 'wb') as f:
    #                         f.write(attachment.read())

    #                     task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
    #                     task_attachments.append(task_attachment)
    #                 except Exception as e:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": status.HTTP_400_BAD_REQUEST,
    #                         "message": "Failed to create Task.",
    #                         "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
    #                     })

    #             serializer.save()

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_201_CREATED,
    #                 "message": "Task created successfully.",
    #                 "data": {
    #                     "task": serializer.data,
    #                     "attachments": [attachment.attachment for attachment in task_attachments]
    #                 }
    #             })
    #         else:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to create Task.",
    #                 "errors": serializer.errors
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })


    

    # @csrf_exempt
    # def create_task(self, request):
    #     serializer = BoardCheckListTaskSerializer(data=request.data)

    #     try:
    #         if serializer.is_valid():
    #             checklist_id = request.data.get('checklist')  # Assuming you have the checklist ID in the request data
    #             if not checklist_id:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_400_BAD_REQUEST,
    #                     "message": "Invalid request. checklist_id is missing."
    #                 })

                
    #             max_sequence = Tasks.objects.filter(checklist_id=checklist_id).aggregate(Max('sequence'))['sequence__max']
    #             if max_sequence is not None:
    #                 max_sequence = Decimal(max_sequence)
    #                 sequence = str(int(max_sequence) + 1)
    #             else:
    #                 sequence = "1"

    #             task = serializer.save(sequence=sequence)  

    #             assign_user_ids = request.data.get('assign_to', [])
    #             if assign_user_ids:
    #                 assign_users = User.objects.filter(id__in=assign_user_ids)
    #                 task.assign_to.set(assign_users)

    #             attachments = request.FILES.getlist('attachments')
    #             user_folder = settings.MEDIA_ROOT
    #             task_attachments = []
    #             for attachment in attachments:
    #                 try:
    #                     file_name = ''.join(random.choices('0123456789', k=8)) + '_' + attachment.name
    #                     file_path = '/employee/task_attachment/' + file_name
    #                     with open(user_folder + file_path, 'wb') as f:
    #                         f.write(attachment.read())

    #                     task_attachment = TaskAttachments.objects.create(task=task, attachment=file_path)
    #                     task_attachments.append(task_attachment)
    #                 except Exception as e:
    #                     return JsonResponse({
    #                         "success": False,
    #                         "status": status.HTTP_400_BAD_REQUEST,
    #                         "message": "Failed to create Task.",
    #                         "errors": f"Failed to process attachment: {attachment.name}. Error: {str(e)}"
    #                     })

    #             serializer.save()

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_201_CREATED,
    #                 "message": "Task created successfully.",
    #                 "data": {
    #                     "task": serializer.data,
    #                     "attachments": [attachment.attachment for attachment in task_attachments]
    #                 }
    #             })
    #         else:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to create Task.",
    #                 "errors": serializer.errors
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })


    


    @csrf_exempt
    def updateTaskData(self, request):
        task_id = request.data.get('task_id')
        try:
            task = Tasks.objects.get(id=task_id)
        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "task not found",
            })

        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task updated successfully",
                "data": serializer.data
            })
        return JsonResponse({
            "success": False,
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid data",
            "errors": serializer.errors
        })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('task_id', openapi.IN_QUERY, description="task_id ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 
    @csrf_exempt
    def deleteTaskData(self, request):
        task_id = request.data.get('task_id')
        print(task_id)
        try:
            checklist = Tasks.objects.get(id=task_id)
        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Tasks not found",
            })

        checklist.delete()
        return JsonResponse({
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Tasks deleted successfully",
        })  
    

    @csrf_exempt
    def getTaskData(self, request):
        try:
            task = Tasks.objects.all()
            serializer = TaskSerializer(task, many=True)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task retrieved successfully",
                "data": serializer.data
            })
        except TemplateChecklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task Attachment not found."
            })
    

    @csrf_exempt
    def getUserTasks(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            tasks = Tasks.objects.filter(assign_to=user_id)
            serializer = TaskSerializer(tasks, many=True)
            data = serializer.data

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks retrieved successfully.",
                "data": data
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user tasks.",
                "errors": str(e)
            })
        
    @csrf_exempt
    def getUserCreatedTasks(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            tasks = Tasks.objects.filter(created_by=user_id)
            serializer = TaskSerializer(tasks, many=True)
            data = serializer.data

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User tasks retrieved successfully.",
                "data": data
            })

        except Exception as e:
            return JsonResponse({   
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user tasks.",
                "errors": str(e)
            })
