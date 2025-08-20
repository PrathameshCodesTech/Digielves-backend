
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from configuration.gzipCompression import compress
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import random
from django.conf import settings
import re

import fitz  
from transformers import pipeline

class AiViewSet(viewsets.ModelViewSet):

    
    @csrf_exempt
    def GetSummery(self, request):
        


        type= request.data['type']
        if type == "text":
            transcript_text = request.POST.get("input_text", "")
            print(transcript_text)    
        elif type == "vtt":
        
            uploaded_file = request.FILES.get('reports')
            print(uploaded_file)

            # Save the uploaded .vtt file in the media root directory
            user_folder = settings.MEDIA_ROOT
            filename = '/transcript_summary/report_' + ''.join(random.choices('0123456789', k=8)) + '.vtt'
            file_path = user_folder + filename
            print(file_path)
    
            with open(file_path, 'wb') as vtt_file:
                vtt_file.write(uploaded_file.read())
    
            # Read the .vtt file using your read_vtt_file function
            subtitles = read_vtt_file(file_path)
    
            # Combine the subtitle text into a single transcript
            transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
            print(transcript_text)

            
        
        else:
            file = request.FILES.get('reports')
            user_folder = settings.MEDIA_ROOT

            filename =  '/transcript_summary/report_' + ''.join(random.choices('0123456789', k=8))   + '_' + '.txt'
                            
            with open(user_folder + filename, 'wb') as f:
                                
                f.write(file.read())

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

 
        response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Summery Retrived successfully.",
                "summary": summary,
                "action_items" : action_items
            }

        return compress(response)
        


    @csrf_exempt
    def GetDoctorSummery(self, request):
        
        try:
            
            if "pdf_file" not in request.FILES:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "PDF file not found in the request."
                })

            
            pdf_file = request.FILES["pdf_file"]
            
            
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            pdf_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                pdf_text += page.get_text()

            
            model_name = "Andyrasika/summarization_model"
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            input_ids = tokenizer.encode(pdf_text, return_tensors="pt", max_length=1024, truncation=True)
            summary_ids = model.generate(input_ids, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            response = {
                "success": True,
                "status": 200,
                "message": "Summary retrieved successfully.",
                "summary": summary
            }

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "An error occurred while processing the request.",
                "error": str(e)
            })
        
        
    @csrf_exempt
    def GetSummery_from_pdf(self, request):    
            
        try:    
            
            if "pdf_file" not in request.FILES:
                return JsonResponse({
                    "success": False,
                    "status": 400,
                    "message": "PDF file not found in the request."
                })

            
            pdf_file = request.FILES["pdf_file"]
            
            
            pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
            pdf_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                pdf_text += page.get_text()

            
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(pdf_text, max_length=150, min_length=50, do_sample=False)

            response = {
                "success": True,
                "status": 200,
                "message": "Summary retrieved successfully.",
                "summary": summary[0]["summary_text"]
            }
            

            return compress(response)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "status": 500,
                "message": "An error occurred while processing the request.",
                "error": str(e)
            })




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