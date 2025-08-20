
from digielves_setup.models import Board, Checklist
from employee.seriallizers.board_seriallizer import BoardCheckListSerializer, BoardCheckListTaskSerializer, BoardSerializer, BoardCheckListForAddSerializer

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from employee.views.board_checklist_task import BoardCheckListTaskViewSet
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Max
from decimal import Decimal
import math
class BoardCheckListViewSet(viewsets.ModelViewSet):

    serializer_class = BoardCheckListSerializer
    
    

    

    @csrf_exempt
    def AddBoardCheckList(self, request):
      
        serializer = BoardCheckListForAddSerializer(data=request.data)
        try:
            if serializer.is_valid():
                board_id = request.data.get('board')  
                if not board_id:
                    print("🐍 File: views/board_checklist.py | Line: 33 | AddBoardCheckList ~ board_id",board_id)
                    
                    return JsonResponse({
                        "success": False,
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Invalid request. board_id is missing."
                    })

                
                max_sequence = Checklist.objects.filter(board=board_id).aggregate(Max('sequence'))['sequence__max']

                if max_sequence is not None:
                    if max_sequence == "NaN":
                        
                        serializer.validated_data['sequence'] = "5"
                    else:
                        
                        max_sequence = Decimal(max_sequence)
                        serializer.validated_data['sequence'] = str(int(max_sequence) + 1)
                else:
                    
                    serializer.validated_data['sequence'] = "5"

                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Board created successfully.",
                    "data": serializer.data
                })
            else:
                print("🐍 File: views/board_checklist.py | Line: 68 | AddBoardCheckList ~ serializer.errors",serializer.errors)
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Failed to create Board.",
                    "errors": serializer.errors
                })
                    
        except Exception as e:
            print("🐍 File: views/board_checklist.py | Line: 76 | AddBoardCheckList ~ str(e)",str(e))
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error.",
                "errors": str(e)
            })

    
    # commented on 25 july

    # @csrf_exempt
    # def AddBoardCheckList(self, request):
    #     print("-------------------------------------")
    #     print(request.data)
    #     serializer = BoardCheckListSerializer(data=request.data)
    #     try:
    #         if serializer.is_valid():
    #             max_sequence = Checklist.objects.aggregate(Max('sequence'))['sequence__max']
    #             print(max_sequence)
    #             if max_sequence is not None:
                   
    #                 if max_sequence == "NaN":
    #                     print("--r-----")

    #                     serializer.validated_data['sequence'] = "1"
    #                 else:
                        
    #                     max_sequence = Decimal(max_sequence)
    #                     serializer.validated_data['sequence'] = str(int(max_sequence) + 1)
    #                     print("0000---")
    #                     print(max_sequence)
    #             else:
    #                 print("--999999---")
    #                 serializer.validated_data['sequence'] = "1"

    #             serializer.save()
    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_201_CREATED,
    #                 "message": "Board created successfully.",
    #                 "data": serializer.data
    #             })
    #         else:
    #             print("-----krdo")
                
    #             serializer.validated_data['sequence'] = "1"

    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to create Board.",
    #                 "errors": serializer.errors
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })




# commented on 24 july 4.10
    # @csrf_exempt
    # def AddBoardCheckList(self, request):
    #     print("-----")
    #     print(request.data)
    #     serializer = BoardCheckListSerializer(data=request.data)
    #     try:
    #         if serializer.is_valid():
                
    #             max_sequence = Checklist.objects.aggregate(Max('sequence'))['sequence__max']
    #             if max_sequence is not None:
    #                 max_sequence = Decimal(max_sequence)
                    
    #                 serializer.validated_data['sequence'] = str(int(max_sequence) + 1)
    #             else:
                    
    #                 serializer.validated_data['sequence'] = "1"

    #             serializer.save()
    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_201_CREATED,
    #                 "message": "Board created successfully.",
    #                 "data": serializer.data
    #             })
    #         else:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Failed to create Board.",
    #                 "errors": serializer.errors
    #             })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Internal server error.",
    #             "errors": str(e)
    #         })


            

    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('board_id', openapi.IN_QUERY, description="Board ID parameter", type=openapi.TYPE_INTEGER,default=2)
    ]) 
    @csrf_exempt
    def getBoardCheckList(self ,request):
        try:
            board_id = request.GET.get('board_id')
            print(board_id)
            if board_id:
                board = Checklist.objects.filter(board_id=board_id)
                serializer = BoardCheckListSerializer(board,many=True)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board check list retrieved successfully",
                    "data": {
                        "board_checklist": serializer.data
                    }
                })
            else:
                boards = Checklist.objects.all()
                serializer = BoardCheckListSerializer(boards, many=True)
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Boards check list retrieved successfully",
                    "data": {
                        "board_checklist": serializer.data
                    }
                })
        except Checklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board check list not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to retrieve Boards check list",
                "errors": str(e)
            })
        
  
    @csrf_exempt
    def updateBoard(self, request):
        try:
            check_id = request.data.get('check_id')
            if not check_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. check_id is missing."
                })

            checklist = Checklist.objects.filter(id=check_id).first()
            if not checklist:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Board Check List not found."
                })

            serializer = BoardCheckListSerializer(checklist, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Board Check List updated successfully.",
                    
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
                "message": "Failed to update Board Check List.",
                "errors": str(e)
            })


    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('check_id', openapi.IN_QUERY, description="Board check_id ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 
    def deleteBoardCheckList(self,request):
        try:
            check_id = request.GET.get('check_id')
            print(check_id)
            board_check= Checklist.objects.get(id=check_id)
            board_check.delete()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Board check deleted successfully",
            })
        except Board.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Board check not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete Board check",
                "errors": str(e)
            })
        

    @csrf_exempt
    def updateChecklistSequence(self, request):
        try:
            checklist_id = request.data.get('checklist_id')
            sequence = request.data.get('sequence')

            if not checklist_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. checklist_id is missing."
                })

            checklist = Checklist.objects.get(id=checklist_id)

            

            if float(sequence) <= 0.000005:
                board = checklist.board
                
                checklists_in_board = Checklist.objects.filter(board=board).order_by('sequence')

                
                new_sequence = 5
                for checklist_in_board in checklists_in_board:
                    checklist_in_board.sequence = new_sequence
                    checklist_in_board.save()
                    new_sequence += 1
            else:
                checklist.sequence = sequence
                checklist.save()

            serializer = BoardCheckListSerializer(checklist)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Checklist sequence updated successfully.",
                "data": serializer.data
            })

        except Checklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update checklist sequence.",
                "errors": str(e)
            })






                
    @csrf_exempt
    def update_task_checklist(self, request):
        print(request.data)
        try:
            user_id = request.data.get('user_id')
            task_id = request.data.get('task_id')
            checklist_id = request.data.get('checklist_id')
            sequence = request.data.get('sequence')  # Get the new sequence value from the request

            if not (user_id and task_id and checklist_id):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. user_id, task_id, and checklist_id are required."
                })

            task = Tasks.objects.get(id=task_id)

            if user_id not in [str(task.created_by.id)] + list(task.assign_to.values_list('id', flat=True)):
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "User is not authorized to update the task's checklist."
                })

            checklist = Checklist.objects.get(id=checklist_id)
            
            # Check if the sequence field is provided in the request and update the checklist sequence if present
            if sequence is not None:
                if float(sequence) <= 0.000005:
                    # Create a new sequence for the task in the checklist
                    checklist_tasks = Tasks.objects.filter(checklist=checklist).order_by('sequence')
                    new_sequence = 5.0
                    for task_in_checklist in checklist_tasks:
                        task_in_checklist.sequence = new_sequence
                        task_in_checklist.save()
                        new_sequence += 1.0
                    task.sequence = new_sequence
                else:
                    # Update the checklist's sequence
                    checklist.sequence = sequence
                    checklist.save()

            task.checklist = checklist
            task.save()

            response = {
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Task's checklist updated successfully.",
                "data": {
                    "task_id": task_id,
                    "checklist_id": checklist_id
                }
            }

            return JsonResponse(response)

        except Tasks.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Task not found.",
            })
        except Checklist.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Checklist not found.",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to update task's checklist.",
                "errors": str(e)
            })
