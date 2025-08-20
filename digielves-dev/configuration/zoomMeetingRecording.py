
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
from digielves_setup.models import DoctorConsultation, DoctorConsultationDetails, DoctorPersonalDetails, DoctorPrescriptions, EmployeePersonalDetails

import time

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


def getTeamRecording(zoom_meet_id, meet_id, consultation_id):
    try:
        print("-------------------------------------------------------------56 (getTeamRecording)")
        print(zoom_meet_id)
        zoom_api_url = f"https://api.zoom.us/v2/meetings/{zoom_meet_id}/recordings"
        print(consultation_id)
        print(zoom_api_url)

        zoom_api_token = get_zoom_access_token()
        print("---------")
        
        print(zoom_api_token)


        headers = {
            'Authorization': f'Bearer {zoom_api_token}',
        }


        response = requests.get(zoom_api_url, headers=headers)
        print("-------71-----------------------------------------hey")
        a=response.json
        print(a)
        print(response.status_code)
        
        if response.status_code == 200:
            data = response.json()

            
            last_recording = data['recording_files'][-1]
            audio_recording = data['recording_files'][-3]  
            print("-------------------------------------------------------------------------85")
            print(last_recording)
            print(audio_recording)
            print("-------------------------------------------------------------------------88")
            
            response = requests.get(last_recording['download_url'],headers=headers)
            response_recording = requests.get(audio_recording['download_url'],headers=headers)
            
            
            
            audio_path=""
            transcript_path=""
            
            print(response_recording)
            
            
            if response_recording.status_code == 200:
                try:
                    print("-------------------------------------------------------------------------102")
                    extension = audio_recording['file_extension']
                    audio_path =f'employee/audio_recording/{zoom_meet_id}.{extension.lower()}'
                    save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                    print(save_path)
                    print("-------------------------------------------------------------------------107")
                    
                    with open(save_path, 'wb') as file:
                        file.write(response_recording.content)
                    
                    print("-------------------------------------------------------------------------112")
                except:
                    pass
                
                
            else:
                print("Error downloading recording.")
                print("-------------------------------------------------------------------------117")
    
            
            
            
            if response.status_code == 200:


                extension = last_recording['file_extension']
                transcript_path = f'employee/transcript/{zoom_meet_id}.{extension.lower()}'
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
        
                
                summary_ids = model.generate(input_ids, max_length=400, min_length=150, length_penalty=2.0, num_beams=4, early_stopping=True)

                summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

                prescription_pattern = r"diet|prescription|medication|prevent|avoid|tretment|advice|follow up|need|take|recommend|recommends|recover|precaution|precautions|advised|suggests|prescribing|will take|prescribe|prescribed|prescribed him|prescribing him|prescribed her|prescribed them"

                exclus_prescription_pattern = r"were took|were advised|were suggests|were prescribed|were prescribed him|were prescribing him|were prescribed her|were prescribed them"

                output_summary = ""
                prescription_precaution = ""
                for sentence in summary.split("."):
                    # print(sentence)

                    matches = re.search(prescription_pattern, sentence, re.IGNORECASE)  
                    try:
                        if matches.group() is not None:
                            inclusive = True
                    except:
                        inclusive = False

                    matches = re.search(exclus_prescription_pattern, sentence, re.IGNORECASE)  

                    try:
                        if matches.group() is not None:
                            exclusive = True
                    except:
                        exclusive = False
                        

                    if inclusive and ~exclusive   :
                        prescription_precaution += sentence + ". "
                    elif len(sentence) > 3:
                        output_summary += sentence + ". "
                consultation = DoctorConsultation.objects.get(id =consultation_id )
                consultation.meeting_transcript = transcript_text
                consultation.meeting_summery = output_summary
                consultation.precaution = prescription_precaution 
                consultation.summery_got=True
                consultation.summery_generating=False
                consultation.save()
                print(consultation.meeting_summery)


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
                        try:
                            extension = audio_recording['file_extension']
                            audio_path =f'employee/audio_recording/{zoom_meet_id}.{extension.lower()}'
                            save_path = os.path.join(settings.MEDIA_ROOT, f'employee/audio_recording/{meet_id}.{extension.lower()}')
                            print(save_path)
                            
                            with open(save_path, 'wb') as file:
                                file.write(response_recording.content)
                        except:
                            pass
                        
                        
                        
                        
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

                
                        summary_ids = model.generate(input_ids, max_length=400, min_length=150, length_penalty=2.0, num_beams=4, early_stopping=True)

                        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

                        prescription_pattern = r"diet|prescription|medication|prevent|avoid|tretment|advice|follow up|need|take|recommend|recommends|recover|precaution|precautions|advised|suggests|prescribing|will take|prescribe|prescribed|prescribed him|prescribing him|prescribed her|prescribed them"

                        exclus_prescription_pattern = r"were took|were advised|were suggests|were prescribed|were prescribed him|were prescribing him|were prescribed her|were prescribed them"

                        output_summary = ""
                        prescription_precaution = ""
                        for sentence in summary.split("."):
                            # print(sentence)

                            matches = re.search(prescription_pattern, sentence, re.IGNORECASE)  
                            try:
                                if matches.group() is not None:
                                    inclusive = True
                            except:
                                inclusive = False

                            matches = re.search(exclus_prescription_pattern, sentence, re.IGNORECASE)  

                            try:
                                if matches.group() is not None:
                                    exclusive = True
                            except:
                                exclusive = False
                                

                            if inclusive and ~exclusive   :
                                prescription_precaution += sentence + ". "
                            elif len(sentence) > 3:
                                output_summary += sentence + ". "  
                        #return   transcript_text, output_summary, prescription_precaution  
                        consultation = DoctorConsultation.objects.get(id =consultation_id )
                        consultation.meeting_transcript = transcript_text
                        consultation.meeting_summery = output_summary
                        consultation.precaution = prescription_precaution 
                        consultation.summery_got=True
                        consultation.save()
                        print(consultation.meeting_summery)
                             

        
                    else:
                        print("Error downloading transcribe.")

            if retry_count >= max_retries:
                print("Max retries reached. Handle accordingly.")
        else:
            print("error Zoom API request. Status code:", response.status_code)

    except Exception as e:
        print("------")
        print(e)


     
        

