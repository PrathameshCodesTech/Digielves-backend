from django.template import Template
from digielves_setup.models import Board, SavedTemplateChecklist, SavedTemplates, TestSavedTemplate, TemplateAttachments

from employee.seriallizers.template_seriallizers import *
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import pandas as pd

class TemplateViewSet(viewsets.ModelViewSet):

    serializer_class = TemplateSerializer
    
    @csrf_exempt
    def AddCategory(self,request):
        print(request.data)
        file = request.data.get('excel_file')
        category_names = request.data.get('category_names', None)

        if file:
            try:
                
                df = pd.read_excel(file)

                
                categories = df['Category'].tolist()

                
                for category_name in categories:
                    Category.objects.create(name=category_name.strip())

                return JsonResponse(
                    {"success": True, "status": status.HTTP_201_CREATED, "message": "Categories added successfully"},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return JsonResponse(
                    {"success": False, "status": status.HTTP_400_BAD_REQUEST, "message": "Failed to add categories", "errors": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif category_names:
            try:
                
                category_names = category_names.split(',')

                
                for category_name in category_names:
                    Category.objects.create(name=category_name)

                return JsonResponse(
                    {"success": True, "status": status.HTTP_201_CREATED, "message": "Categories added successfully"},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return JsonResponse(
                    {"success": False, "status": status.HTTP_400_BAD_REQUEST, "message": "Failed to add categories", "errors": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return JsonResponse(
                {"success": False, "status": status.HTTP_400_BAD_REQUEST, "message": "No data provided (file or category names)"},
                status=status.HTTP_400_BAD_REQUEST
            )
            


    @csrf_exempt
    def add_template_from_excel(self,request):
        try:
            excel_file = request.FILES.get('excel_file')
            
            if excel_file:
                
                df = pd.read_excel(excel_file)
    
                created_templates = []
    
                for _, row in df.iterrows():
                    category_name = row['Category'].strip().lower()
                    template_name = row['Template Name']
    
                    
                    try:
                        #category = Category.objects.get(name=category_name)
                        category = Category.objects.get(name__iexact=category_name)
                    except Category.DoesNotExist:
                        print("--------------does not exist")
                        print(category_name)
                        
                        continue
    
                    template = Template(category=category, template_name=template_name.strip())
                    template.save()
                    created_templates.append(template.id)
    
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Templates added successfully",
                    "data": {
                        "created_templates": created_templates
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Excel file not provided"
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add templates from Excel",
                "errors": str(e)
            })
    
    
    
    
    @csrf_exempt
    def add_template_checklists_from_excel(self,request):
        try:
            excel_file = request.FILES.get('excel_file')
    
            if excel_file:
                df = pd.read_excel(excel_file)
    
                created_checklists = []
    
                for _, row in df.iterrows():
                    template_name = row['Template Name'].strip()
                    section_name = str(row['Section Name']).strip()
                    
                    
                    #print(f"Template Name from Excel: {template_name}")
    
                    # Modify this part to filter templates case-insensitively
                    templates = Template.objects.filter(template_name__iexact=template_name)
                    
                    if templates.exists():
                        template = templates.first() 
                    else:
                        print("----sdcdsgcdshdshbj-----")
                        print(template_name)
                        continue
                        
    
                    try:
                        template_checklist = TemplateChecklist(template=template, name=section_name)
                        template_checklist.save()
                        created_checklists.append(template_checklist.id)
                    except ValidationError as e:
                          
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Validation error while adding Template Checklist",
                            "errors": str(e),
                        })
    
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Template Checklists added successfully",
                    "data": {
                        "created_checklists": created_checklists,
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Excel file not provided",
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add Template Checklists from Excel",
                "errors": str(e),
            })
            
    
    
    @csrf_exempt
    def add_template_task_lists_from_excel(self, request):
        try:
            excel_file = request.FILES.get('excel_file')
    
            if excel_file:
                df = pd.read_excel(excel_file)
    
                created_task_lists = []
    
                for _, row in df.iterrows():
                    template_checklist_name = row['Section Name'].strip()
                    task_name = str(row['Tasks']).strip()
    
                    checklist = TemplateChecklist.objects.filter(name__iexact=template_checklist_name).first()
    
                    if checklist is None:
                        print(f"Checklist with name '{template_checklist_name}' does not exist.")
                        continue
    
                    try:
                        template_task_list = TemplateTaskList(checklist=checklist, task_name=task_name)
                        template_task_list.save()
                        created_task_lists.append(template_task_list.id)
                    except ValidationError as e:
                        return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Validation error while adding Template Task List",
                            "errors": str(e),
                        })
    
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,
                    "message": "Template Task Lists added successfully",
                    "data": {
                        "created_task_lists": created_task_lists,
                    }
                })
            else:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Excel file not provided",
                })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to add Template Task Lists from Excel",
                "errors": str(e),
            })



    @csrf_exempt
    def AddTemplate(self,request):
        print(request.data)
        template_obj=Template()
        template = TemplateSerializer(template_obj,data=request.data)

        if template.is_valid(raise_exception=True):
            try:
                response = template.save()

                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_201_CREATED,                
                    "message": "Template Added successfully",
                    "data": {
                        'template_id' : response.id
                    }
                    }) 
            
            except Exception as e:
                    return JsonResponse({
                            "success": False,
                            "status": status.HTTP_400_BAD_REQUEST, 
                            "message": "Failed to register user",
                            "errors": str(e)
                            })
            

    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('template_id', openapi.IN_QUERY, description="Template ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 


    @csrf_exempt
    def template(self, request):
        if request.method != 'GET':
            return JsonResponse({
                "success": False,
                "status": status.HTTP_405_METHOD_NOT_ALLOWED,
                "message": "Only GET requests are allowed."
            })
        
        try:
            user_id = request.GET.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "user_id is required."
                })
            
            templates = Template.objects.all()
            categories = Category.objects.all()
            categories_dict = {category.id: category.name for category in categories}
            
            sorted_data = []
            category_templates = {}
            
            for template in templates:
                category_id = template.category_id
                category_name = categories_dict.get(category_id, "Uncategorized")
                template_data = {
                    "id": template.id,
                    "template_name": template.template_name,
                }
                
                attachment_queryset = TemplateAttachments.objects.filter(template=template)
                attachment_serializer = TemplateAttachmentsSerializers(attachment_queryset, many=True)
                attachment_data = attachment_serializer.data
                template_data['attachments'] = attachment_data
                
                if category_id not in category_templates:
                    category_templates[category_id] = {"category": category_name, "templates": []}
                
                category_templates[category_id]["templates"].append(template_data)
            
            for category_id, category_data in category_templates.items():
                sorted_data.append({
                    "category_id": category_id,
                    "category": category_data["category"],
                    "templates": category_data["templates"]
                })

            # Fetch saved templates for the user
            saved_templates = SavedTemplates.objects.filter(category__user_id=user_id)
            saved_templates_dict = {}
            
            for saved_template in saved_templates:
                category_id = saved_template.category_id
                category_name = saved_template.category.name
                template_data = {
                    "id": saved_template.id,
                    "template_name": saved_template.template_name,
                    # "checklists": []
                }
                
                # saved_checklists = saved_template.saved_checklist.all()
                # for saved_checklist in saved_checklists:
                #     checklist_data = {
                #         "id": saved_checklist.id,
                #         "name": saved_checklist.name,
                #         "tasks": []
                #     }
                    
                #     saved_tasks = saved_checklist.saved_task.all()
                #     for saved_task in saved_tasks:
                #         task_data = {
                #             "id": saved_task.id,
                #             "task_name": saved_task.task_name
                #         }
                #         checklist_data["tasks"].append(task_data)
                    
                #     template_data["checklists"].append(checklist_data)
                
                if category_id not in saved_templates_dict:
                    saved_templates_dict[category_id] = {"category": category_name, "templates": []}
                
                saved_templates_dict[category_id]["templates"].append(template_data)
            
            saved_template_data = []
            for category_id, category_data in saved_templates_dict.items():
                saved_template_data.append({
                    "category_id": category_id,
                    "category": category_data["category"],
                    "templates": category_data["templates"]
                })
            
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Templates retrieved successfully",
                "data": sorted_data,
                "saved_template": saved_template_data
            })
        
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred.",
                "errors": str(e)
            })
            
    
#    @csrf_exempt
#    def template(self, request):
#        try:
#            template_id = request.GET.get('template_id')
#            if template_id:
#                template = Template.objects.get(id=template_id)
#                serializer = TemplateSerializer(template)
#    
#                checklists = TemplateChecklist.objects.filter(template_id=template_id)
#                checklist_serializer = TemplateCheckListSerializer(checklists, many=True)
#                checklists_data = checklist_serializer.data
#    
#                for checklist_data in checklists_data:
#                    checklist_id = checklist_data['id']
#                    tasklists = TemplateTaskList.objects.filter(checklist_id=checklist_id)
#                    tasklist_serializer = TemplateCheckListTaskSerializer(tasklists, many=True)
#                    tasklists_data = tasklist_serializer.data
#    
#                    checklist_attachments = TemplateAttachments.objects.filter(template_id=template_id)
#                    attachment_serializer = TemplateAttachmentsSerializers(checklist_attachments, many=True)
#    
#                    checklist_data['tasklists'] = tasklists_data
#                    checklist_data['attachments'] = attachment_serializer.data
#    
#                response_data = {
#                    "template": serializer.data,
#                    "checklists": checklists_data,
#                }
#    
#                return JsonResponse({
#                    "success": True,
#                    "status": status.HTTP_200_OK,
#                    "message": "Template details retrieved successfully",
#                    "data": response_data
#                })
#            else:
#                # Fetch all templates and their categories
#                templates = Template.objects.all()
#                categories = Category.objects.all()
#                categories_dict = {category.id: category.name for category in categories}
#    
#                sorted_data = {}
#                for template in templates:
#                    category_name = categories_dict.get(template.category_id, "Uncategorized")  # Get category name or use "Uncategorized" if not found
#                    template_data = {
#                        "id": template.id,
#                        "template_name": template.template_name
#                    }
#    
#                    # Fetch attachments for the template
#                    attachment_queryset = TemplateAttachments.objects.filter(template=template)
#                    attachment_serializer = TemplateAttachmentsSerializers(attachment_queryset, many=True)
#                    attachment_data = attachment_serializer.data
#                    template_data['attachments'] = attachment_data
#    
#                    if category_name not in sorted_data:
#                        sorted_data[category_name] = []
#    
#                    sorted_data[category_name].append(template_data)
#    
#                return JsonResponse({
#                    "success": True,
#                    "status": status.HTTP_200_OK,
#                    "message": "Categories retrieved successfully",
#                    "data": {
#                        "categories": sorted_data
#                    }
#                })
#        except Template.DoesNotExist:
#            return JsonResponse({
#                "success": False,
#                "status": status.HTTP_404_NOT_FOUND
#            })


    
    # @csrf_exempt
    # def template(self, request):
    #     try:
    #         template_id = request.GET.get('template_id')
    #         if template_id:
    #             template = Template.objects.get(id=template_id)
    #             serializer = TemplateSerializer(template)

    #             checklists = TemplateChecklist.objects.filter(template_id=template_id)
    #             checklist_serializer = TemplateCheckListSerializer(checklists, many=True)
    #             checklists_data = checklist_serializer.data

    #             for checklist_data in checklists_data:
    #                 checklist_id = checklist_data['id']
    #                 tasklists = TemplateTaskList.objects.filter(checklist_id=checklist_id)
    #                 tasklist_serializer = TemplateCheckListTaskSerializer(tasklists, many=True)
    #                 tasklists_data = tasklist_serializer.data

    #                 checklist_data['tasklists'] = tasklists_data

    #             response_data = {
    #                 "template": serializer.data,
    #                 "checklists": checklists_data
    #             }

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_200_OK,
    #                 "message": "Template details retrieved successfully",
    #                 "data": response_data
    #             })
    #         else:
    #             templates = Template.objects.all()
    #             serializer = TemplateSerializer(templates, many=True)

    #             return JsonResponse({
    #                 "success": True,
    #                 "status": status.HTTP_200_OK,
    #                 "message": "Templates retrieved successfully",
    #                 "data": {
    #                     "templates": serializer.data
    #                 }
    #             })
    #     except Template.DoesNotExist:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_404_NOT_FOUND,
    #             "message": "Template not found",
    #         })
    #     except Exception as e:
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "Failed to retrieve template details",
    #             "errors": str(e)
    #         })



    @csrf_exempt
    def updateTemplate(self, request):
        try:
            template_id = request.data.get('template_id')
            print(template_id)
            if not template_id:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid request. template_id is missing."
                })
            
            template = Template.objects.filter(id=template_id).first()
            if not template:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Template not found."
                })
            
            serializer = TemplateSerializer(template, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "success": True,
                    "status": status.HTTP_200_OK,
                    "message": "Template updated successfully.",
                    "data": {
                        "template": serializer.data
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
                "message": "Failed to update template.",
                "errors": str(e)
            })



    @swagger_auto_schema(manual_parameters=[
    openapi.Parameter('template_id', openapi.IN_QUERY, description="Template ID parameter", type=openapi.TYPE_INTEGER,default=1)
    ]) 
    def deleteTemplate(self,request):
        try:
            template_id = request.GET.get('template_id')
            print(template_id)
            template = Template.objects.get(id=template_id)
            template.delete()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Template deleted successfully",
            })
        except Template.DoesNotExist:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Template not found",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Failed to delete template",
                "errors": str(e)
            })


    @csrf_exempt
    def add_template_attachment(self, request):
        print(request.data)
        try:


            attachment = request.FILES.get('attachment')
            template_id = request.data.get('template')

            if not attachment or not template_id:
                return JsonResponse({"message": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)

            file_name = attachment.name
            file_path = 'template/template_attachments/' + file_name
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            saved_file = fs.save(file_path, attachment)

            template_attachment = TemplateAttachments(template_id=template_id, attachment=saved_file)
            template_attachment.save()
            return JsonResponse({
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Attchment successfully.",
                
            })
       
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while raising the issue.",
                "errors": str(e)
            })
    @csrf_exempt
    def update_attachment(self,request):
        try:
            attachment_id = request.data.get('attachment_id')

            template_attachment = TemplateAttachments.objects.get(id=attachment_id)
            print(template_attachment)
        except TemplateAttachments.DoesNotExist:
            return JsonResponse({"message": "Template attachment not found"}, status=status.HTTP_404_NOT_FOUND)

        attachment = request.FILES.get('attachment')

        if attachment:
            file_name = attachment.name
            file_path = 'template/template_attachments/' + file_name
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            saved_file = fs.save(file_path, attachment)
            template_attachment.attachment = saved_file

        template_id = request.data.get('template')
        if template_id:
            template_attachment.template_id = template_id

        template_attachment.save()

        serializer = TemplateAttachmentsSerializers(template_attachment)

        return JsonResponse({"message": "Template attachment updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)





class GetTaskTemplateViewSet(viewsets.ModelViewSet):
    
    def get_template_details(self, request):
        try:
            template_id = request.GET.get('template_id')
            user_id = request.GET.get('user_id')
            from_saved_template = request.GET.get('from_saved_template', False)

            if not template_id and user_id:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Template ID and user_id is required."
                })

            try:
                template_id = int(template_id)
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "Invalid Template ID format."
                })

            if from_saved_template == 'true' or from_saved_template == True or from_saved_template == "True":
                print("-----------------------chamke-------------------")
                try:
                    saved_temp = SavedTemplates.objects.get(id = template_id)
                except SavedTemplates.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": 404,
                        "message": "emplate not fund."
                    })
                checklists = SavedTemplateChecklist.objects.filter(template=saved_temp)

                checklists_serializer = SavedTemplateChecklistSerializer(checklists, many=True)
            else:
                print("-----------------------jakiya-------------------")
                try:
                    template = Template.objects.get(id=template_id)
                except Template.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "status": 404,
                        "message": "Template not foun."
                    })

                checklists = TemplateChecklist.objects.filter(template=template)

                checklists_serializer = TemplateChecklistSerializer(checklists, many=True)
            
            

            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Data retrieved successfully.",
                "data": checklists_serializer.data
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "An error occurred.",
                "errors": str(e)
            })
