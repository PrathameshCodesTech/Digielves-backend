
from configuration.zoom_utils import get_zoom_access_token
import requests
import json
import os
import uuid
from django.http import JsonResponse
from django.conf import settings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import pipeline
import re
from requests.auth import HTTPBasicAuth
from digielves_setup.models import Meettings, MeettingSummery, DoctorConsultation, DoctorConsultationDetails, DoctorPersonalDetails, DoctorPrescriptions, EmployeePersonalDetails

import time
from configuration.team_utils import get_teams_access_token


def read_vtt_file(file_path):
    print("read vtt")
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


def getTeamsRecording(team_meet_id, meeting_id):
    try:
        print("---------------------------------------------------------------------------------------------------------------jfjjfjfjjfjjfjfjfjf")
        print(team_meet_id)
        



        team_recording_api_url = f"https://graph.microsoft.com/beta/users/f89f9418-a72f-4d28-a0a7-33ddcd0fc325/onlineMeetings/{team_meet_id}/recordings"
        team_transcript_api_url = f"https://graph.microsoft.com/beta/users/f89f9418-a72f-4d28-a0a7-33ddcd0fc325/onlineMeetings/{team_meet_id}/transcripts"

        bearer_tokens=get_teams_access_token()
        print(bearer_tokens)

        headers = {
            'Authorization': f'Bearer {bearer_tokens}',
        }





        print(team_transcript_api_url)
        response = requests.get(team_recording_api_url, headers=headers)
        print("==" * 100)
        print(response)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(data)
    
    
                recording_response = requests.get(team_recording_api_url, headers=headers)
                print("::" * 100)
                print(recording_response.json())
                recording_data  = recording_response.json()
                
                meeting_recording = recording_data['value'][0]['recordingContentUrl']
         
                
    
                response_video_recording = requests.get(meeting_recording,headers=headers)
                video_path = ""
    
    
                if response_video_recording.status_code == 200:
                    
                    video_path =f'employee/video_recording/{team_meet_id}_teams.mp4'
                    save_path = os.path.join(settings.MEDIA_ROOT, f'employee/video_recording/{team_meet_id}_teams.mp4')
                    print(save_path)
    
                    with open(save_path, 'wb') as file:
                        file.write(response_video_recording.content)
      
                else:
                    print("Error downloading recording.")
            except Exception as e:
                print("Error--------------------------------112 line")

            response = requests.get(team_transcript_api_url, headers=headers)

            data = response.json()
            
            print("----------------------------hmmmmmmmmmmm"*3)
            print(data['value'])
            meeting_transcript = data['value'][0]['transcriptContentUrl']
            print(meeting_transcript)
            
            meeting_transcript += "?$format=text/vtt"
            response = requests.get(meeting_transcript,headers=headers)
            
            audio_path=""
            transcript_path=""
            print("=1=" * 100)

            print(response)


            
            if response.status_code == 200:


                transcript_path = f'employee/transcript/{team_meet_id}.vtt'
                save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{team_meet_id}.vtt')
                print(save_path)
                print(response.content)
                
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                
                subtitles = read_vtt_file(save_path)
                print(subtitles)
    
                transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
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
            "discuss",
            "report",
            "reports"
        ]
        
                action_pattern = r"(?:\b(?:action|task|item|work|to do|asked to|suggests to|will be|will schedule|will make|discuss|shares|meeting)\b[\s:-]*[\s]*[\w\s]+)"
                

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
                

                meettings_instance = Meettings.objects.get(id=meeting_id)
                meettings_instance.summery_got=True
                meettings_instance.save()
                

                save_meet_summery = MeettingSummery(
                    meettings=meettings_instance,
                    meet_transcript=transcript_path,
                    meet_summery=summary,
                    #meet_video = video_path,

                    meet_tasks=action_items
                )
                save_meet_summery.save()
        

            else:
                print("Error downloading transcribe.")
        elif response.status_code==404:
            print("Error in Zoom API request. Status code:", response.status_code)
            
            
            
            retry_count = 0
            max_retries = 10

            while retry_count < max_retries:
                retry_count += 1

                # Sleep for 15 minutes (900 seconds)
                print("Retrying API call after  minutes...")
                time.sleep(600)

                print(team_transcript_api_url)
                response = requests.get(team_transcript_api_url, headers=headers)
                print("==" * 100)
                print(response)
                
                if response.status_code == 200:
                    data = response.json()
                    print(data)

                    
                    meeting_transcript = data['value'][0]['transcriptContentUrl']
                    print(meeting_transcript)
                    
                    meeting_transcript += "?$format=text/vtt"
                    response = requests.get(meeting_transcript,headers=headers)
                    
                    audio_path=""
                    transcript_path=""
                    print("=1=" * 100)

                    print(response)


                    
                    if response.status_code == 200:

                        recording_response = requests.get(team_recording_api_url, headers=headers)
                        print("::" * 100)
                        print(recording_response.json())
                        recording_data  = recording_response.json()
                        meeting_recording = recording_data['value'][0]['recordingContentUrl']
                
                        

                        response_video_recording = requests.get(meeting_recording,headers=headers)
                        video_path = ""


                        if response_video_recording.status_code == 200:
                            try:
                                video_path =f'employee/video_recording/{team_meet_id}_teams.mp4'
                                save_path = os.path.join(settings.MEDIA_ROOT, f'employee/video_recording/{team_meet_id}_teams.mp4')
                                print(save_path)

                                with open(save_path, 'wb') as file:
                                    file.write(response_video_recording.content)
                            except:
                                pass
                        else:
                            print("Error downloading recording.")



                        transcript_path = f'employee/transcript/{team_meet_id}.vtt'
                        save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{team_meet_id}.vtt')
                        print(save_path)
                        print(response.content)
                        
                        with open(save_path, 'wb') as file:
                            file.write(response.content)
                        
                        subtitles = read_vtt_file(save_path)
                        print(subtitles)
            
                        transcript_text = "\n".join(subtitle['text'] for subtitle in subtitles)
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
                    "discuss",
                    "report",
                    "reports"
                ]
                
                        action_pattern = r"(?:\b(?:action|task|item|work|to do|asked to|suggests to|will be|will schedule|will make|discuss|shares|meeting)\b[\s:-]*[\s]*[\w\s]+)"
                        
        
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
                        
        
                        meettings_instance = Meettings.objects.get(id=meeting_id)
                        
                        
                        save_meet_summery = MeettingSummery(
                            meettings=meettings_instance,
                            meet_transcript=transcript_path,
                            meet_summery=summary,
                            meet_video = video_path,
                            meet_tasks=action_items
                        )
                        save_meet_summery.save()
                
        
                    else:
                        print("Error downloading transcribe.")
                    break

            if retry_count >= max_retries:
                print("Max retries reached. Handle accordingly.")
        else:
            print("error Zoom API request. Status code:", response.status_code)

    except Exception as e:
        print("------")
        print(e)


     
        

