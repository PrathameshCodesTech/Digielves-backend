
from rest_framework import viewsets
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import status
from configuration.gzipCompression import compress


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

from django.core.files.uploadedfile import UploadedFile
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from io import BytesIO
import librosa
from transformers import pipeline
import numpy as np

from pydub import AudioSegment
import subprocess
from django.conf import settings



class AiAudioAndTransriptViewSet(viewsets.ModelViewSet):

    @csrf_exempt
    def get_summery(self, request):
        try:
            # Check if the request contains an audio fil
            if "audio_file" not in request.FILES:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Audio file not found in the request."
                })

            # Handle the audio file (you can save it to storage or process it as needed)
            audio_file: UploadedFile = request.FILES.get('audio_file')

            # Read the audio file content as a byte stream
            audio_data = audio_file.read()
            # print(audio_data)

            model_name = "openai/whisper-large-v2"
            processor = WhisperProcessor.from_pretrained(model_name)
            model = WhisperForConditionalGeneration.from_pretrained(model_name)

            # Load the audio data using librosa to get the sampling rate
            audio_data, sr = librosa.load(BytesIO(audio_data), sr=16000)
              # Replace with the correct sampling rate
            print(audio_data)
            print(sr)

            # Transcribe the audio
            audio_input = processor(audio_data.tolist(), return_tensors="pt", sampling_rate=sr)  # Convert to list
            input_values = audio_input.input_values 
             # Correctly access input values
            print(input_values)
            transcription = model.generate(input_values)

            # Decode the transcription
            transcription_text = processor.batch_decode(transcription, skip_special_tokens=True)
            
            
            
            
            tokenizer = AutoTokenizer.from_pretrained("slauw87/bart_summarisation")
            model = AutoModelForSeq2SeqLM.from_pretrained("slauw87/bart_summarisation")
    
            
            input_ids = tokenizer.encode(transcript_text, return_tensors="pt", max_length=1024, truncation=True)
    
            
            summary_ids = model.generate(input_ids, max_length=300, min_length=150, length_penalty=3.0, num_beams=4, early_stopping=True)
            print("---------")
    
            
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

            response = {
                "success": True,
                "status": status.HTTP_201_CREATED,
                "message": "Summary retrieved successfully.",
                "transcript": transcription_text
            }

            return JsonResponse(response)
        except Exception as e:
            # print(e)
           
          
            exception_type = type(e).__name__
            error_message = str(e)
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing the request.",
                "error": str(e)
            })
