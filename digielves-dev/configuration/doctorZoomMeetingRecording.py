
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


def getTeamRecording(zoom_meet_id, consultation_id):
    try:
        print("lagnalu------")
        print(meet_id)
        zoom_api_url = f"https://api.zoom.us/v2/meetings/{meet_id}/recordings"

        zoom_api_token = get_zoom_access_token()


        headers = {
            'Authorization': f'Bearer {zoom_api_token}',
        }


        response = requests.get(zoom_api_url, headers=headers)
        print("-----hey")
        a=response.json
        print(a)
        
        if response.status_code == 200:
            data = response.json()

            
            last_recording = data['recording_files'][-1]
            audio_recording = data['recording_files'][-3]  
            
            response = requests.get(last_recording['download_url'],headers=headers)
            response_recording = requests.get(audio_recording['download_url'],headers=headers)
            
            audio_path=""
            transcript_path=""
            
            print(response_recording)
            
            
            if response_recording.status_code == 200:
                extension = audio_recording['file_extension']
                audio_path =f'employee/audio_recording/{meet_id}.{extension.lower()}'
                save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                print(save_path)

                with open(save_path, 'wb') as file:
                    file.write(response_recording.content)
                
                
                
                
            else:
                print("Error downloading recording.")
    
            
            
            
            if response.status_code == 200:


                extension = last_recording['file_extension']
                transcript_path = f'employee/transcript/{meet_id}.{extension.lower()}'
                save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{meet_id}.{extension.lower()}')
                print(save_path)


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
                

                meettings_instance = Meettings.objects.get(id=ids)
                
                
                save_meet_summery = MeettingSummery(
                    meettings=meettings_instance,
                    meet_audio=audio_path,
                    meet_transcript=transcript_path,
                    meet_summery=summary,
                    meet_tasks=action_items
                )
                save_meet_summery.save()
        

            else:
                print("Error downloading transcribe.")
        elif response.status_code==404:
            print("Error in Zoom API request. Status code:", response.status_code)
            
            
            
            retry_count = 0
            max_retries = 3  

            while retry_count < max_retries:
                retry_count += 1

                # Sleep for 15 minutes (900 seconds)
                print("Retrying API call after  minutes...")
                time.sleep(1200)

                response = requests.get(zoom_api_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()

            
                    last_recording = data['recording_files'][-1]
                    audio_recording = data['recording_files'][-3]  
                    
                    response = requests.get(last_recording['download_url'],headers=headers)
                    response_recording = requests.get(audio_recording['download_url'],headers=headers)
                    
                    audio_path=""
                    transcript_path=""
                    
                    print(response_recording)
                    
                    
                    if response_recording.status_code == 200:
                        extension = audio_recording['file_extension']
                        audio_path =f'employee/audio_recording/{meet_id}.{extension.lower()}'
                        save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                        print(save_path)
        
                        with open(save_path, 'wb') as file:
                            file.write(response_recording.content)
                        
                        
                        
                        
                    else:
                        print("Error downloading recording.")
            
                    
                    
                    
                    if response.status_code == 200:
        
        
                        extension = last_recording['file_extension']
                        transcript_path = f'employee/transcript/{meet_id}.{extension.lower()}'
                        save_path = os.path.join(settings.MEDIA_ROOT, f'employee/transcript/{meet_id}.{extension.lower()}')
                        print(save_path)
        
        
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
                        
        
                        meettings_instance = Meettings.objects.get(id=ids)
                        
                        
                        save_meet_summery = MeettingSummery(
                            meettings=meettings_instance,
                            meet_audio=audio_path,
                            meet_transcript=transcript_path,
                            meet_summery=summary,
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


     
        

