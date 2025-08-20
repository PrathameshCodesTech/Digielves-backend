import json
from configuration.gzipCompression import compress

from digielves_setup.helpers.error_trace import create_error_response
from digielves_setup.models import Board, BoardPermission, Checklist, FevBoard, SubTasks, EmployeePersonalDetails, TaskChecklist, TaskInBoardPermission, TaskStatus, Tasks, TemplateChecklist, TemplateTaskList, User,Template, Notification, Redirect_to, UserFilters, notification_handler
from employee.seriallizers.board_seriallizer import AddBoardSerializer, BoardCheckListSerializer, BoardPermissionGivenUsersSerializer, BoardPermissionSerializer, BoardSerializer, BoardSerializers, GetBoardsSerializer, GetChecklistTasksSerializers, TaskBoardPermissionGivenUsersSerializer

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from employee.views.controllers.status_controllers import get_status_ids_from_creater_side
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from employee.seriallizers.task_seriallizers import SectionSerializer, TaskSerializer, TaskSerializerForBoard
from django.db.models import Case, When, Value, CharField, IntegerField,FloatField
from django.db.models.functions import Cast
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.functions import Lower
from datetime import datetime, timedelta, timezone
import pytz
from django.db.models.signals import post_save
from django.utils import timezone as newTimezone


class BoardViewSet(viewsets.ModelViewSet):

    serializer_class = BoardSerializer
    
    

    
    @csrf_exempt
    def AddBoard(self, request):
        serializer = AddBoardSerializer(data=request.data)
        user = User.objects.get(id=request.data.get("created_by"))
        
        try:
            if serializer.is_valid():
                board = serializer.save()
                assign_user_ids_str = request.data.get('assign_to', '')

                
                # Split the comma-separated string of user IDs and convert them to integers.
                if assign_user_ids_str:
                    assign_user_ids = [int(user_id) for user_id in assign_user_ids_str.split(',') if user_id.strip()] 
                    
                    
                    assign_users = User.objects.filter(id__in=assign_user_ids)
                    board.assign_to.set(assign_users)
                    
                    # Notification Implementation
                    try:
                        

                        # Additional Notification Implementation
                        post_save.disconnect(notification_handler, sender=Notification)
                        notification = Notification.objects.create(
                            user_id=request.user,
                            where_to="customBoardMain",
                            notification_msg=f"You have been assigned a board: {board.board_name}",
                            action_content_type=ContentType.objects.get_for_model(Board),
                            action_id=board.id
                        )
                        
                        notification.notification_to.set(assign_users)
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)

                        Redirect_to.objects.create(notification=notification, link="/employee/customBoardMain")
                    except Exception as e:
                        print("Error sending WebSocket notification:", e)
                        
                outsider_user_ids_str = request.data.get('access_to', '') 
                
                if outsider_user_ids_str:
                    outsider_user_ids = [int(user_id) for user_id in outsider_user_ids_str.split(',') if user_id.strip()] 
                    
                    for access_to_id in outsider_user_ids:
                        
                        access_to_user = User.objects.get(id=access_to_id)
                        
                        BoardPermission.objects.create(
                            user=user,
                            access_to=access_to_user,
                            board=board,
                            can_view_board = True
                        )                
    
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Board created successfully.",
                    "data": serializer.data
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Board.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })






            

    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('user_id', openapi.IN_QUERY, description="USER ID parameter", type=openapi.TYPE_INTEGER,default=105)
    ]) 
    @csrf_exempt
    def getBoard(self, request):
        try:
            created_by_id = request.GET.get('created_by')
            user_id = request.GET.get('user_id')
            template_id = request.GET.get('template_id')

            if user_id:
                user = User.objects.get(id=user_id)
                boards = Board.objects.filter(assign_to=user)
            elif created_by_id:
                created_by_user = User.objects.get(id=created_by_id)
                boards = Board.objects.filter(created_by=created_by_user)
            elif template_id:
                boards = Board.objects.filter(template_id=template_id)
            else:
                boards = Board.objects.all()

            serializer = BoardSerializer(boards, many=True)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Boards retrieved successfully",
                "data": {
                    "Boards": serializer.data
                }
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found",
            })

        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Boards",
                "errors": str(e)
            })

    @csrf_exempt
    def update_board_due_date(self, request):
        try:
            board_id = request.data.get('board_id')
            user_id = request.data.get('user_id')

            if not (board_id and user_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. task_id and user_id are required."
                })

            board = Board.objects.get(id=board_id,created_by = user_id)

            
            due_date = request.data.get('due_date')
            if due_date is not None:
                board.due_date = due_date

                
            board.save()
            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "board updated successfully."
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update task.",
                "errors": str(e)
            })

    @csrf_exempt
    def getBoards(self, request):
        try:
            user_id = request.GET.get('user_id')

            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id is missing."
                })

            boards_created_by = list(Board.objects.filter(created_by=user_id))
            boards_assigned_to = list(Board.objects.filter(assign_to=user_id))
            task_boards = list(Board.objects.filter(checklist__tasks__assign_to=user_id))
            sub_task_boards = list(Board.objects.filter(checklist__tasks__subtasks__assign_to=user_id))
            sub_task_child_boards = list(Board.objects.filter(checklist__tasks__subtasks__subtaskchild__assign_to=user_id))

            # Combine the lists and remove duplicates while preserving order
            combined_boards_dict = {board.id: board for board in (boards_created_by + boards_assigned_to + task_boards + sub_task_boards + sub_task_child_boards)}
            combined_boards = list(combined_boards_dict.values())

            # Sort the combined boards alphabetically by board_name
            sorted_boards = sorted(combined_boards, key=lambda x: x.board_name.lower())

            serializer = GetBoardsSerializer(sorted_boards, many=True)
            data = serializer.data

            response_data = {
                "boards": [],
            }

            for board_data in data:
                board_id = board_data['id']

                get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)

                task_statuses = TaskStatus.objects.filter(organization=get_org_id.organization_id).order_by('order')
                
                tasks_count = []
                for Status in task_statuses:
                    status_name = Status.status_name.lower()  # Convert to lowercase for consistent comparison
                    tasks = Tasks.objects.filter(
                        Q(created_by=user_id) | Q(assign_to=user_id),
                        inTrash=False,
                        checklist__board_id=board_id,
                        status=Status
                    )
                    tasks_count.append({
                        "status": status_name,
                        "count": tasks.count(),
                        "color": Status.color  # Include status color
                    })

                board_data["tasks_count"] = tasks_count
                response_data["boards"].append(board_data)

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "User Boards retrieved successfully.",
                "data": response_data
            }

            return JsonResponse(response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve user boards.",
                "errors": str(e)
            })


# by user filterd
    # @csrf_exempt
    # def getBoards(self, request):
    #     try:
    #         user_id = request.GET.get('user_id')

    #         if not user_id:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Invalid request. user_id is missing."
    #             })

    #         boards_created_by = Board.objects.filter(created_by=user_id)
    #         boards_assigned_to = Board.objects.filter(assign_to=user_id)

            
    #         if boards_created_by.exists() and boards_assigned_to.exists():
    #             boards = boards_created_by | boards_assigned_to
    #         elif boards_created_by.exists():
    #             boards = boards_created_by
    #         elif boards_assigned_to.exists():
    #             boards = boards_assigned_to
    #         else:
    #             boards = []

    #         serializer = BoardSerializer(boards, many=True)
    #         data = serializer.data

    #         # Include task count in the response
    #         response_data = {
    #             "boards": data,
                
    #         }

    #         response={
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "User Boards retrieved successfully.",
    #             "data": response_data
    #         }
            
    #         return compress(response)

    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to retrieve user boards.",
    #             "errors": str(e)
    #         })

    @csrf_exempt
    def UpdateBoard(self, request):
        try:    
            board_id = request.data.get('board_id')
            user_id = request.data.get('user_id')
            template_id = request.data.get('template_id')
      
            board = Board.objects.get(id=board_id)
            if template_id:
                try:
                    template = Template.objects.get(id=template_id)
                    board.template = template
                    board.save()
                    Checklist.objects.filter(board=board).delete()
                    Tasks.objects.filter(checklist__board=board).delete()
                    
                    template_checklists = TemplateChecklist.objects.filter(template=template)
                    for index, template_checklist in enumerate(template_checklists, start=5):
                    
                        checklist = Checklist.objects.create(
                            board=board,
                            name=template_checklist.name,
                            sequence=str(index)
                        )

                        
                        template_tasklists = TemplateTaskList.objects.filter(checklist=template_checklist)
                        for index, template_tasklist in enumerate(template_tasklists, start=5):
                            Tasks.objects.create(
                                created_by=board.created_by,
                                checklist=checklist,
                                task_topic=template_tasklist.task_name,
                                sequence=str(index)
                            )
                    
                    # static_checklists = ['In Progress', 'Completed', 'Done']
                    # for static_checklist_name in static_checklists:
                    #     Checklist.objects.create(board=board, name=static_checklist_name)

                except Template.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Template not found",
                    })

            serializer = BoardSerializer(board)
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Board updated successfully",
                "data": serializer.data
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update board",
                "errors": str(e)
            })


    # @csrf_exempt
    # def UpdateBoard(self, request):
    #     try:    
    #         board_id = request.data.get('board_id')
    #         template_id = request.data.get('template_id')

    #         board = Board.objects.get(id=board_id)
    #         if template_id:
    #             try:
    #                 template = Template.objects.get(id=template_id)
    #                 board.template = template
    #                 board.save()
    #                 Checklist.objects.filter(board=board).delete()
    #                 Tasks.objects.filter(checklist__board=board).delete()
                    
    #                 template_checklists = TemplateChecklist.objects.filter(template=template)
    #                 for template_checklist in template_checklists:
    #                     checklist = Checklist.objects.create(board=board, name=template_checklist.name)

                        
    #                     template_tasklists = TemplateTaskList.objects.filter(checklist=template_checklist)
    #                     for template_tasklist in template_tasklists:
    #                         Tasks.objects.create(
    #                             created_by=board.created_by,
    #                             checklist=checklist,
    #                             task_topic=template_tasklist.task_name
    #                         )
    #                 # static_checklists = ['In Progress', 'Completed', 'Done']
    #                 # for static_checklist_name in static_checklists:
    #                 #     Checklist.objects.create(board=board, name=static_checklist_name)


    #             except Template.DoesNotExist:
    #                 return JsonResponse({
    #                     "success": False,
    #                     "status": status.HTTP_404_NOT_FOUND,
    #                     "message": "Template not found",
    #                 })

    #         serializer = BoardSerializer(board)
    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Board updated successfully",
    #             "data": serializer.data
    #         })
    #     except Board.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Board not found",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to update board",
    #             "errors": str(e)
    #         })


    @csrf_exempt
    def UpdateBoardAssignTo(self, request):
        try:
            board_id = request.data.get('board_id')
            user_id = request.data.get('user_id')
            board = Board.objects.get(id=board_id)
            if board_id:

                try:
                    
                    existing_assign_users = set(board.assign_to.all())

                    
                    assign_to_values = request.data.get('assign_to')
                    new_assign_user_ids = [int(id) for id in assign_to_values.split(",")]

                    new_assign_users = User.objects.filter(id__in=new_assign_user_ids)

                    
                    # existing_assign_users.update(new_assignx_users)

                    try:    
                        post_save.disconnect(notification_handler, sender=Notification)
                        
                        # Get currently assigned users
                        current_assigned_users = set(board.assign_to.all())

                        # Determine new users to notify
                        new_users_to_notify = [user for user in new_assign_users if user not in current_assigned_users]
                        user_intance = User.objects.get(id=user_id)
                        notification = Notification.objects.create(
                            user_id=user_intance,
                            where_to="customBoardMain",
                            notification_msg=f"You have been assigned a board: {board.board_name}",
                            action_content_type=ContentType.objects.get_for_model(Board),
                            action_id=board.id,
                            
                        )
                        

                        notification.notification_to.set(new_users_to_notify)
                            
                            
                        post_save.connect(notification_handler, sender=Notification)
                        post_save.send(sender=Notification, instance=notification, created=True)
                    except Exception as e:
                        print("-------------error",str(e))
                        pass
                    board.assign_to.set(new_assign_users)
                    board.save()

                except Template.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Template not found",
                    })

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Board updated successfully",
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update board",
                "errors": str(e)
            })




#   old
    @csrf_exempt
    def updateBoard(self, request):
        try:
            board_id = request.data.get('board_id')
            if not board_id:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid request. board_id is missing."
                })

            board = Board.objects.filter(id=board_id).first()
            if not board:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Board not found."
                })

            serializer = BoardSerializer(board, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board updated successfully.",
                    "data": {
                        "board": serializer.data
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid data provided.",
                    "errors": serializer.errors
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update Board.",
                "errors": str(e)
            })

    # old
    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('board_id', openapi.IN_QUERY, description="Board ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 
    def deleteBoard(self,request):
        try:
            board_id = request.GET.get('board_id')
            board = Board.objects.get(id=board_id)
            board.delete()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Board deleted successfully",
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Board",
                "errors": str(e)
            })

    def serialize_status_info(self,status_info):
        return {
            "id": status_info["id"],
            "status_name": status_info["status_name"],
            "color": status_info["color"],
        }

    @csrf_exempt
    def GetCustomBoardData(self, request):
        try:
            board_id = request.GET.get('board_id')
            user_id = request.GET.get('user_id')

            if board_id:
                board = Board.objects.get(id=board_id)
                serializer = BoardSerializers(board)

                checklist_data = []
                checklists = Checklist.objects.filter(board_id=board_id).order_by('sequence', 'created_at') 
                for checklist in checklists:
                    sequence_ordering = Case(
                    When(sequence__regex=r'^\d+(\.\d+)?$', then=Cast('sequence', FloatField())),
                    When(sequence__regex=r'^\d+$', then=Cast('sequence', IntegerField())),
                    default=Value(0),
                    output_field=IntegerField()
                    
                )
                    assigned_checklist_tasks = SubTasks.objects.filter(
                    assign_to=user_id).values_list('Task', flat=True).distinct()
                    
                    tasklists = Tasks.objects.filter(
                        inTrash=False,
                    # id__in=parent_tasks.values_list('id', flat=True),
                    checklist_id=checklist.id
                    ).order_by(sequence_ordering, 'sequence')
                    
                    if user_id:
                        tasklists = tasklists.filter( 
                                                     Q(Q(checklist_id__board__assign_to=user_id) 
                                                       | Q(checklist_id__board__created_by=user_id) 
                                                       | Q(assign_to = user_id) 
                                                       | Q(subtasks__assign_to=user_id)
                                                       | Q(subtasks__subtaskchild__assign_to=user_id)))
                        
                        

                    tasklist_serializer = TaskSerializerForBoard(tasklists, many=True)
                    tasks_data = []
                    encountered_tasks = set()  # To keep track of encountered task IDs

                    closed_status_ids = get_status_ids_from_creater_side(user_id, True)
                    for task in tasklist_serializer.data:
                        task_id = f"t_{task['id']}"

                        if task_id not in encountered_tasks:
                            tasks = Tasks.objects.get(id=task['id'])
 
                           
                            
                            created_by_id = task["created_by"]
                            created_by_instance = User.objects.get(id=created_by_id)
                            
                            created_by_data = {
                                "id": created_by_instance.id,
                                "email": created_by_instance.email,
                                "firstname": created_by_instance.firstname,
                                "lastname": created_by_instance.lastname,
                            }
                            
                            
                            status_id = tasks.status
                            if status_id:
                                # If status_id is not None, set the status_info dictionary with the provided status details
                                status_info = {
                                    "id": status_id.id,
                                    "status_name": status_id.status_name,
                                    "color": status_id.color,
                                }  
                            else:
                                # If status_id is None, handle it as follows:
                                
                                # Retrieve the user's organization ID based on the provided user_id
                                get_org_id = EmployeePersonalDetails.objects.get(user_id=user_id)
                                
                                # Get the first TaskStatus for the user's organization that has fixed_state as "Pending"
                                task_status = TaskStatus.objects.filter(organization=get_org_id.organization_id,fixed_state="Pending").order_by('order').first()
                                
                                # Set the status_info dictionary with the task status details from the organization
                                status_info = {
                                    "id": task_status.id,
                                    "status_name": task_status.status_name,
                                    "color": task_status.color,
                                }
                                
                                # Update the task's status to the task_status retrieved for the user's organization
                                tasks.status= task_status
                                tasks.save()
                                
                            if task["due_date"]:
                                IST = pytz.timezone('Asia/Kolkata')
                
                                # due_date_ist = task["due_date"].astimezone(IST)
                                if isinstance(task["due_date"], str):
                                    # Convert string to datetime object
                                    due_date_utc = datetime.fromisoformat(task["due_date"]).astimezone(IST)
                                
                                    
                                tasks_data.append({
                                    "id": task_id,
                                    "sequence": task["sequence"],
                                    "task_topic": task["task_topic"],
                                    "task_description": task["task_description"],
                                    "task_status": status_info,
                                    "urgent_status":task["urgent_status"],
                                    "task_due_date": due_date_utc.strftime('%Y-%m-%d %H:%M:%S%z'),
                                    "task_created_at": task["created_at"],
                                    "task_assign_to": task["assign_to"],
                                    "task_created_by": created_by_data,
                               
                                })
                            else:
                                tasks_data.append({
                                    "id": task_id,
                                    "sequence": task["sequence"],
                                    "task_topic": task["task_topic"],
                                    "task_description": task["task_description"],
                                    "task_status": status_info,
                                    "urgent_status":task["urgent_status"],
                                    "task_due_date": None,
                                    "task_created_at": task["created_at"],
                                    "task_assign_to": task["assign_to"],
                                    "task_created_by": created_by_data,
                      
                                })
                            encountered_tasks.add(task_id)
                    checklist_data.append({
                        "id": f"c_{checklist.id}",
                        "title": checklist.name,    
                        "tasks": tasks_data,
                        "sequence": checklist.sequence,
                    })

                response_data = []
                for checklist in checklist_data:
                    
                    section = {
                        "id": checklist["id"],
                        "title": checklist["title"],
                        "tasks": checklist["tasks"],
                        "sequence": checklist["sequence"],  # Include the sequence in the response
                    }
                    response_data.append(section)
                
                try:
                    board_view = UserFilters.objects.get(user=user_id).custom_board_view
                except Exception as e:
                    board_view = None

                response = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board details retrieved successfully",
                    "board": serializer.data,
                    "data": response_data,
                    "board_view" : board_view
                }

                return compress(response)
            else:
                boards = Board.objects.all()
                serializer = BoardSerializer(boards, many=True)
                response = {
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Boards retrieved successfully",
                    "data": {
                        "boards": serializer.data
                    }
                }
                return compress(response)
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve board details",
                "errors": str(e)
            })
    # @csrf_exempt
    # def Board(self, request):
    #     try:
    #         board_id = request.GET.get('board_id')
    #         user_id = request.GET.get('user_id')

    #         if board_id:
    #             board = Board.objects.get(id=board_id)
    #             serializer = BoardSerializers(board)

    #             checklist_data = []
    #             checklists = Checklist.objects.filter(board_id=board_id).order_by('sequence', 'created_at') 
    #             for checklist in checklists:
    #                 sequence_ordering = Case(
    #                 When(sequence__regex=r'^\d+(\.\d+)?$', then=Cast('sequence', FloatField())),
    #                 When(sequence__regex=r'^\d+$', then=Cast('sequence', IntegerField())),
    #                 default=Value(0),
    #                 output_field=IntegerField()
                    
    #             )
    #                 assigned_checklist_tasks = ChecklistTasks.objects.filter(
    #                 assign_to=user_id).values_list('task_checklist__Task', flat=True).distinct()
                    
    #                 parent_tasks = Tasks.objects.filter(
    #             id__in=assigned_checklist_tasks,checklist__board_id=board_id).order_by(sequence_ordering, 'sequence')
    #                 print(parent_tasks)
                    
                    
    #                 tasklists = Tasks.objects.filter(
    #                 # id__in=parent_tasks.values_list('id', flat=True),
    #                 checklist_id=checklist.id
    #             ).order_by(sequence_ordering, 'sequence')
                    
    #                 print("-------------------------hmmm") 
    #                 print(tasklists)

    #                 if user_id:
    #                     tasklists = tasklists.filter(Q(assign_to=user_id) | Q(created_by=user_id))

    #                 tasklist_serializer = TaskSerializerForBoard(tasklists, many=True)
    #                 tasks_data = []
    #                 encountered_tasks = set()  # To keep track of encountered task IDs

    #                 for task in tasklist_serializer.data:
    #                     task_id = f"t_{task['id']}"
    #                     if task_id not in encountered_tasks:
                            
    #                         tasks_data.append({
    #                             "id": task_id,
    #                             "sequence": task["sequence"],
    #                             "task_topic": task["task_topic"],
    #                             "task_description": task["task_description"],
    #                             "task_status": task["status"],
    #                             "task_due_date": task["due_date"],
    #                             "task_assign_to": task["assign_to"],
    #                             "task_created_by": task["created_by"],
                                
    #                         })
    #                         encountered_tasks.add(task_id)

    #                 checklist_data.append({
    #                     "id": f"c_{checklist.id}",
    #                     "title": checklist.name,
    #                     "tasks": tasks_data,
    #                     "sequence": checklist.sequence,
    #                 })

    #             response_data = []
    #             for checklist in checklist_data:
                    
    #                 section = {
    #                     "id": checklist["id"],
    #                     "title": checklist["title"],
    #                     "tasks": checklist["tasks"],
    #                     "sequence": checklist["sequence"],  # Include the sequence in the response
    #                 }
    #                 response_data.append(section)

    #             response = {
    #                 "success": True,
    #                 "status": status.HTTP_200_OK,
    #                 "message": "Board details retrieved successfully",
    #                 "board": serializer.data,
    #                 "data": response_data
    #             }

    #             return compress(response)
    #         else:
    #             boards = Board.objects.all()
    #             serializer = BoardSerializer(boards, many=True)
    #             response = {
    #                 "success": True,
    #                 "status": status.HTTP_200_OK,
    #                 "message": "Boards retrieved successfully",
    #                 "data": {
    #                     "boards": serializer.data
    #                 }
    #             }
    #             return compress(response)
    #     except Board.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Board not found",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to retrieve board details",
    #             "errors": str(e)
    #         })











    # @csrf_exempt
    # def get_users(self, request):
    #     user_id = request.GET.get('user_id')
    #     org_id = request.GET.get('org_id')
    #     board_id = request.GET.get('board_id')

    #     try:
    #         user = User.objects.get(id=user_id)
    #         employee_details = EmployeePersonalDetails.objects.filter(user_id=user_id, organization_id=org_id,designation="Dev::Employee")

    #         if not employee_details.exists():
    #             response = {
    #                 'success': False,
    #                 'status': 403,
    #                 'message': 'User does not have access to the specified organization.',
    #             }
    #             return JsonResponse(response)

    #         try:
    #             board = Board.objects.get(id=board_id)
    #             assigned_users = board.assign_to.all()
    #             created_by_user = board.created_by
    #             users = User.objects.filter(employeepersonaldetails__organization_id=org_id, verified=1).exclude(id__in=assigned_users).exclude(id=created_by_user.id)

    #             user_data = []
    #             for user in users:
    #                 user_data.append({
    #                     'user_id': user.id,
    #                     'email': user.email,
    #                     'firstname': user.firstname,
    #                     'lastname': user.lastname,
    #                     'phone_no': user.phone_no,
    #                 })

    #             response = {
    #                 'success': True,
    #                 'status': 200,
    #                 'message': 'Users fetched successfully.',
    #                 'data': user_data
    #             }

    #             return compress(response)

    #         except Board.DoesNotExist:
    #             response = {
    #                 'success': False,
    #                 'status': 404,
    #                 'message': 'Board not found.',
    #             }
    #             return JsonResponse(response)

    #     except User.DoesNotExist:
    #         response = {
    #             'success': False,
    #             'status': 404,
    #             'message': 'User not found or not verified.',
    #         }
    #         return JsonResponse(response)

    #     except Exception as e:
    #         response = {
    #             'success': False,
    #             'status': 500,
    #             'message': 'An error occurred while fetching users.',
    #             'error': str(e)
    #         }
    #         return JsonResponse(response)
    
    

    @csrf_exempt
    def get_users(self, request):
        user_id = request.GET.get('user_id')
        org_id = request.GET.get('org_id')
        board_id = request.GET.get('board_id')

        try:
            user = User.objects.get(id=user_id)
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)

            if not employee_details:
                response = {
                    'success': False,
                    'status': 403,
                    'message': 'User does not have access to the specified organization.',
                }
                return JsonResponse(response)

            try:
                board = Board.objects.get(id=board_id)

                
                

                assigned_users = board.assign_to.all()
                created_by_user = board.created_by
                users = User.objects.filter(employeepersonaldetails__organization_id=employee_details.organization_id,employeepersonaldetails__organization_location=employee_details.organization_location, verified=1,user_role="Dev::Employee",active=True).exclude(id__in=assigned_users).exclude(id=created_by_user.id)

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

            except Board.DoesNotExist:
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



   

    
    @csrf_exempt
    def get_users_in_board(self, request):
        user_id = request.GET.get('user_id')
        board_id = request.GET.get('board_id')
        task_id = request.GET.get('task_id')

        try:
            board = Board.objects.get(id=board_id)

            # Retrieve both the creator and assigned users
            assigned_users = list(board.assign_to.all())
            creator = board.created_by
            if creator not in assigned_users:
                assigned_users.append(creator)

            task = None
            if task_id:
                task = Tasks.objects.get(id=task_id)

            unassigned_users = []
            for user in assigned_users:
                if task and task.assign_to.filter(id=user.id).exists():
                    continue
                unassigned_users.append({
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
                'data': unassigned_users
            }

            return compress(response)

        except Board.DoesNotExist:
            response = {
                'success': False,
                'status': 404,
                'message': 'Board not found.',
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
    def get_users_in_board(self, request):
        user_id = request.GET.get('user_id')
        board_id = request.GET.get('board_id')
        task_id = request.GET.get('task_id')

        try:
            board = Board.objects.get(id=board_id)

            # Retrieve both the creator and assigned users
            assigned_users = list(board.assign_to.all())
            creator = board.created_by
            if creator not in assigned_users:
                assigned_users.append(creator)

            task = None
            if task_id:
                task = Tasks.objects.get(id=task_id)

            unassigned_users = []
            for user in assigned_users:
                # Exclude the requester's user ID
                if str(user.id) == user_id:
                    continue

                if task and task.assign_to.filter(id=user.id).exists():
                    continue
                unassigned_users.append({
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
                'data': unassigned_users
            }

            return compress(response)

        except Board.DoesNotExist:
            response = {
                'success': False,
                'status': 404,
                'message': 'Board not found.',
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
    def get_sections(self, request):
        user_id = request.GET.get('user_id')
        board_id = request.GET.get('board_id')

        try:
            user = User.objects.get(id=user_id)
            employee_details = EmployeePersonalDetails.objects.get(user_id=user_id)

            if not employee_details:
                response = {
                    'success': False,
                    'status': 403,
                    'message': 'User does not have access to the specified organization.',
                }
                return JsonResponse(response)

            try:
                board = Board.objects.get(id=board_id)
                sections = Checklist.objects.filter(board=board).order_by('sequence')
                serialized_data = SectionSerializer(sections, many=True)

                response = {
                    'success': True,
                    'status': 200,
                    'message': 'Sections fetched successfully.',
                    'data': serialized_data.data
                }

                return compress(response)

            except Board.DoesNotExist:
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

    
    @csrf_exempt
    def make_favorite(self, request):
        try:
            user_id = request.data.get('user_id')
            board_id = request.data.get('board_id')
            favorite = request.data.get('is_favorite')

            if not user_id or not board_id or favorite is None:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id, board_id and is_favorite are required."
                })

            user = User.objects.get(id=user_id)
            board = Board.objects.get(id=board_id)

            fav_board, created = FevBoard.objects.get_or_create(user=user)
            if created:
                fav_board.board.add(board)

            # Update the favorite status
            if favorite == 'true' or favorite == True or favorite == "True":
                fav_board.board.add(board)
            else:
                fav_board.board.remove(board)


            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Favorite status updated successfully."
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board not found."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed.",
                "errors": str(e)
            })



                
class BoardAccessViewSet(viewsets.ModelViewSet):
    
    @csrf_exempt
    def add_permission(self, request):
        try:
            user_id = request.POST.get('user_id')
            access_to_id = request.POST.get('access_to')
            board_id = request.POST.get('board_id')
            board_access = request.POST.get('board', False)
            checklist_ids = request.POST.get('checklists', '').split(',')

            checklist_ids = [id for id in checklist_ids if id]

            user = User.objects.get(id=user_id)

            try:
                board = Board.objects.filter(
                    Q(id=board_id) & 
                    (Q(created_by=user_id) | Q(assign_to__in=[user_id]))
                ).first()
            except Board.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "error": "Denied",
                    "message": "You don't have permission to give permission."
                }, status=status.HTTP_403_FORBIDDEN)
                    
            if checklist_ids:
                checklists = Checklist.objects.filter(id__in=checklist_ids)

            if board_access == "False" or board_access == "false" or board_access == False:
                access_to_user = User.objects.get(id=access_to_id)
                BoardPermission.objects.filter(access_to=access_to_user, board=board).delete()
                return JsonResponse({
                    "success": True,
                    "message": "Access user removed."
                })

            access_to_user = User.objects.get(id=access_to_id)

            board_permission, created = BoardPermission.objects.get_or_create(
                user=user,
                access_to=access_to_user,
                board=board,
                defaults={'can_view_board': True, 'can_view_checklists': bool(checklist_ids)}
            )

            if not created:
                board_permission.can_view_board = True
                board_permission.can_view_checklists = bool(checklist_ids)

            if checklist_ids:
                board_permission.checklist_permissions.set(checklists)
            else:
                board_permission.checklist_permissions.clear()

            board_permission.save()

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Permissions added successfully."
            })

        except Exception as e:
            return create_error_response(e, status.HTTP_400_BAD_REQUEST)
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add permissions.",
                "errors": str(e)
            })

            
            
    @csrf_exempt
    def get_permission(self, request):
        try:
            user_id = request.GET.get('user_id')
            board_id = request.GET.get('board_id')
            outsider_id = request.GET.get('outsider_id')
            
            
            
            # Fetch user who is requesting permissions
            user = User.objects.get(id=user_id)
            board = Board.objects.get(id=board_id)
            # Fetch all BoardPermissions where the user is either the user or access_to
            if outsider_id:
                permissions = BoardPermission.objects.filter(user=user, board = board, access_to=outsider_id)
            else: 
                permissions = BoardPermission.objects.filter(user=user, board = board)
            
            # Serialize the permissions data
            serializer = BoardPermissionSerializer(permissions, many=True)
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "permissions": serializer.data
            }, safe=False)
            
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to fetch permissions.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def get_permission_given_users(self, request):
        try:
            user_id = request.GET.get('user_id')
            board_id = request.GET.get('board_id')
            
            
            
            # Fetch user who is requesting permissions
            user = User.objects.get(id=user_id)
            board = Board.objects.get(id=board_id)
            # Fetch all BoardPermissions where the user is either the user or access_to
            permissions = BoardPermission.objects.filter(user=user, board = board)
            
            
            # Serialize the permissions data
            serializer = BoardPermissionGivenUsersSerializer(permissions, many=True)
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "permissions": serializer.data
            }, safe=False)
            
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to fetch permissions.",
                "errors": str(e)
            })
            
            
    @csrf_exempt
    def give_task_permissions_in_board(self, request):
        try:                
            user_id = request.data.get('user_id')
            access_to_ids = request.data.get('access_to', '').split(',')
            
            board_id = request.data.get('board_id')
            

            # Fetch user who is granting permission
            user = User.objects.get(id=user_id)
            
            board = Board.objects.get(
                id=board_id
                )
            
            
            if access_to_ids is None or access_to_ids[0] == "":
                # If access_to is not provided or is empty, delete all existing access
                TaskInBoardPermission.objects.filter(user=user, board= board).delete()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "All existing access removed successfully."
                })
                
            for access_to_id in access_to_ids:
                access_to_user = User.objects.get(id=access_to_id)
                TaskInBoardPermission.objects.get_or_create(user = user, access_to = access_to_user,board= board )

            

            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Permissions added successfully."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add permissions.",
                "errors": str(e)
            })
            
    @csrf_exempt
    def get_task_permission_given_users(self, request):
        try:
            user_id = request.GET.get('user_id')
            board_id = request.GET.get('board_id')
            
            
            
            # Fetch user who is requesting permissions
            user = User.objects.get(id=user_id)
            board = Board.objects.get(id=board_id)
            # Fetch all BoardPermissions where the user is either the user or access_to
            permissions = TaskInBoardPermission.objects.filter(user=user, board = board)
            
            
            # Serialize the permissions data
            serializer = TaskBoardPermissionGivenUsersSerializer(permissions, many=True)
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "permissions": serializer.data
            }, safe=False)
            
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found."
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to fetch permissions.",
                "errors": str(e)
            })

    

