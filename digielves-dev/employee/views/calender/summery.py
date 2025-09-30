from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from configuration.gzipCompression import compress
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import random
from django.conf import settings
import re
from digielves_setup.models import SummeryNdTask,User
# import fitz  
from transformers import pipeline
from employee.seriallizers.calender.summery_seriallizers import SummeryNdTaskSerializer
import threading
import uuid
import os


class SummeryAiViewSet(viewsets.ModelViewSet):



    def GetSummery(self,request):
        try:
            type = request.data['type']
            uploaded_file = request.FILES.get('reports')
            user_id = request.data.get("user_id")
            
            
            file_extension = os.path.splitext(uploaded_file.name)[1] 
                    
            summery_task = SummeryNdTask(user_id=user_id, file_name=f'{uploaded_file.name}')
            summery_task.save()

            print(summery_task.id)
            t = threading.Thread(target=long_process_for_summery, args=(type, uploaded_file, user_id,summery_task.id ))
            t.setDaemon(True)
            t.start()
    
            return JsonResponse({
                "success": True,
                "status": 200,
                "message": "Generating...",
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "An error occurred while processing the request.",
                "error": str(e)
            }, status=500)
        
        
    
    
    




    def get_summery_nd_task(self, request):
        user_id = request.GET.get('user_id')  
        print(user_id)
    
        if user_id:
            try:
                
                summery_tasks = SummeryNdTask.objects.filter(user_id=user_id).order_by('-created_at')
                print(summery_tasks)
    
                if summery_tasks:
                    
                    serialized_data = []
                    for summery_task in summery_tasks:
                        serializer = SummeryNdTaskSerializer(summery_task)
                        serialized_data.append(serializer.data)
    
                    
                    response_data = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Data retrieved successfully.",
                        "data": serialized_data
                    }
    
                    return JsonResponse(response_data)
                else:
                    response_data = {
                        "success": True,
                        "status": status.HTTP_200_OK,
                        "message": "Data retrieved successfully.",
                        "data": []
                    }
                    return JsonResponse(response_data)
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": "An error occurred while processing the request.",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse({
                "success": False,
                "message": "user_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)



def read_vtt_file(file_path):
    subtitles = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            
            lines = lines[1:]
            
            
            timestamp = ""
            subtitle = ""
            
            for line in lines:
                line = line.strip()
                
                
                if '-->' in line:
                    timestamp = line
                
                elif not line:
                    if timestamp and subtitle:
                        subtitles.append({"timestamp": timestamp, "text": subtitle})
                        timestamp = ""
                        subtitle = ""
                else:
                    
                    subtitle += line + " "

    except Exception as e:
        print("Error reading .vtt file:", str(e))
    
    return subtitles





def long_process_for_summery(type,uploaded_file,user_id, SummeryNdTask_id):
    print(uploaded_file)
    print("heyyyyyy")
    print(type)
        
        

        
    if type == "text":
    
        transcript_text = request.POST.get("input_text", "")
        print(transcript_text)    
    elif type == "vtt":
    
        print(uploaded_file)
    
        
        print("-------dd---hhh")
        user_folder = settings.MEDIA_ROOT
        file_extension = os.path.splitext(uploaded_file.name)[1] 
        filename = f'/employee/independent_files/{uploaded_file.name[0]}_{uuid.uuid4()}{file_extension}'
        file_path = user_folder + filename
        print(file_path)
        print("----------hhh")
    
        with open(file_path, 'wb') as vtt_file:
            vtt_file.write(uploaded_file.read())
    
        # Read the .vtt file using your read_vtt_file function
        subtitles = read_vtt_file(file_path)
    
        # Combine the subtitle text into a single transcript
        transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
        print(transcript_text)
        
        
        
    
        
    
    else:
        print("-------te ")

        user_folder = settings.MEDIA_ROOT
        file_extension = os.path.splitext(uploaded_file.name)[1] 
        
    
        filename =  f'/employee/independent_files/{uploaded_file.name[0]}_{uuid.uuid4()}{file_extension}'
                        
        with open(user_folder + filename, 'wb') as f:
                            
            f.write(uploaded_file.read())
    
        with open(user_folder + filename , 'r', encoding='utf-8') as file:
            transcript_text = file.read()
        print(transcript_text)
    
    
    
    
    
     
    tokenizer = AutoTokenizer.from_pretrained("slauw87/bart_summarisation")
    model = AutoModelForSeq2SeqLM.from_pretrained("slauw87/bart_summarisation")
    
    
    input_ids = tokenizer.encode(transcript_text, return_tensors="pt", max_length=1024, truncation=True)
    
    
    summary_ids = model.generate(input_ids, max_length=300, min_length=150, length_penalty=3.0, num_beams=4, early_stopping=True)
    print("---------")
    
    
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    
    
    action_keywords = [
    "create",
    "develop",
    "design",
    "implement",
    "deliver",
    "test",
    "analyze",
    "optimize",
    "improve",
    "resolve",
    "complete",
    "project",
    "campaign",
    "report",
    "analysis",
    "proposal",
    "presentation",
    "design",
    "document",
    "code",
    "solution",
    "deadline",
    "timeline",
    "priority",
    "urgent",
    "asap",
    "within the next",
    "by the end of",
    "goal",
    "objective",
    "target",
    "outcome",
    "benefit",
    "requirement",
    "gather",
    "collect",
    "review",
    "validate",
    "approve",
    "launch",
    "monitor",
    "evaluate",
    "scale",
    "maintain",
    "document",
    "communicate",
    "brainstorm",
    "prioritize",
    "estimate",
    "decide",
    "coordinate",
    "collaborate",
    "delegate",
    "coach",
    "mentor",
    "train",
    "manage",
    "troubleshoot",
    "scale",
    "optimize",
    "automate",
    "iterate",
    "experiment",
    "learn",
    "identify",
    "assess",
    "consider",
    "recommend",
    "finalize",
    "optimize",
    "deploy",
    "administer",
    "support",
    "maintain",
    "monitor",
    "evaluate",
    "improve",
    "measure",
    "analyze",
    "report",
    "share",
    "communicate",
    "strategize",
    "plan",
    "budget",
    "forecast",
    "estimate",
    "negotiate",
    "secure",
    "partner",
    "collaborate",
    "integrate",
    "adapt",
    "evolve",
    "transform",
    "discuss"
    ]
    
    action_pattern = r"(?:\b(?:action|task|item|work|to do|asked to|suggests to|will be|will schedule|will make|discuss|shares|meeting)\b[\s:-]*[\s]*[\w\s]+)"
    
    # Combine the existing action pattern with the action keywords
    action_pattern += "|" + "|".join(action_keywords)
    
    
    
    action_items = []
    summary_sentences = summary.split('.')
    for sentence in summary_sentences:
        print(sentence) 
    
        matches = re.search(action_pattern, sentence, re.IGNORECASE)  
        try:
            if matches.group() is not None:
                action_items.append(sentence)
        except:
            inclusive = False
    
    
    
    Summery_Task= SummeryNdTask.objects.get(id=SummeryNdTask_id)
    Summery_Task.summery= summary
    Summery_Task.tasks=action_items
    Summery_Task.summery_generated = True
    Summery_Task.save()
    
    # summery_task = SummeryNdTask(user_id=user_id, summery=summary, tasks=action_items,file_name=uploaded_file)
    # summery_task.save()
    
    
