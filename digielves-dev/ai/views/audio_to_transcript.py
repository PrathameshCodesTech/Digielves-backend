
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
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
#from transformers import WhisperForSpeechRecognition

import soundfile as sf
#from transformers import AutoProcessor, AutoModelForSpeechRecognition
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import transformers
import librosa
import whisper

class AiTransriptViewSet(viewsets.ModelViewSet):


    
    def get_transcript(self, request):
        if "audio_file" not in request.FILES:
            return JsonResponse({
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Audio file not found in the request."
            })
    
        # Handle the audio file (you can save it to storage or process it as needed)
        audio_file = request.FILES.get('audio_file')
    
        # Check the sampling rate of the audio file
        sr = librosa.get_samplerate(audio_file)
    
        # If the format is not recognized (e.g., MP3), convert it to WAV
        if audio_file.content_type != 'audio/wav':
            audio_data, sr = sf.read(audio_file, dtype='int16')
            # Save the audio in WAV format (you can adjust the file name if needed)
            user_folder = settings.MEDIA_ROOT
            filename = '/employee/temp_audio/' + audio_file.name
            file_path = user_folder + filename
            sf.write(file_path, audio_data, sr)
            # Load the converted WAV file
            audio_data, sr = librosa.load(file_path, sr=16000)
        else:
            # Read the audio file content
            audio_data, sr = librosa.load(BytesIO(audio_file.read()), sr=16000)
    
        # Initialize the ASR processor and model


        #processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
        #model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base")

        #processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
        #model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")

    
        # Tokenize and transcribe the audio

        asr_pipeline = transformers.pipeline("automatic-speech-recognition", model="openai/whisper-large-v2", chunk_length_s=30)
        transcription_text = asr_pipeline(audio_data)
        print(transcription_text)
        #input_values = processor(audio_data.tolist(), return_tensors="pt", padding="longest", sampling_rate=sr)

        #with torch.no_grad():
        #    logits = model(input_values.input_values).logits
        #    predicted_ids = torch.argmax(logits, dim=-1)
        #    transcription_text = processor.batch_decode(predicted_ids)
    
        response = {
            "success": True,
            "status": status.HTTP_201_CREATED,
            "message": "Summary retrieved successfully.",
            "transcript": transcription_text # Assuming a single transcription result
        }
    
        return JsonResponse(response)




    
    

    
 




#    def get_transcript(self, request):
#        try:
#            # Check if the request contains an audio file
#            if "audio_file" not in request.FILES:
#                return JsonResponse({
#                    "success": False,
#                    "status": status.HTTP_400_BAD_REQUEST,
#                    "message": "Audio file not found in the request."
#                })
#    
#            # Handle the audio file (you can save it to storage or process it as needed)
#            audio_file = request.FILES.get('audio_file')
#    
#            # Check the sampling rate of the audio file
#            sr = librosa.get_samplerate(audio_file)
#    
#            # If the format is not recognized (e.g., MP3), convert it to WAV
#            if audio_file.content_type != 'audio/wav':
#                audio_data, sr = librosa.load(audio_file, dtype='int16')
#                # Save the audio in WAV format (you can adjust the file name if needed)
#                user_folder = settings.MEDIA_ROOT
#                filename = '/employee/temp_audio/' + audio_file.name
#                file_path = user_folder + filename
#                librosa.output.write_wav(file_path, audio_data, sr)
#                # Load the converted WAV file
#                audio_data, sr = librosa.load(file_path, sr=16000)
#            else:
#                # Read the audio file content
#                audio_data, sr = librosa.load(BytesIO(audio_file.read()), sr=16000)
#    
#            # Initialize the ASR pipeline with "openai/whisper-large-v2" model
#            asr_pipeline = transformers.pipeline("automatic-speech-recognition", model="openai/whisper-large-v2")
#    
#            # Transcribe the audio
#            transcription_text = asr_pipeline(audio_data, sampling_rate=sr)[0]['transcription']
#    
#            response = {
#                "success": True,
#                "status": status.HTTP_201_CREATED,
#                "message": "Summary retrieved successfully.",
#                "transcript": transcription_text
#            }
#    
#            return JsonResponse(response)
#        except Exception as e:
#            # Handle specific errors in a specific way
#            if type(e) == transformers.exceptions.DecodingError:
#                return JsonResponse({
#                    "success": False,
#                    "status": status.HTTP_400_BAD_REQUEST,
#                    "message": "The audio file is not in a supported format."
#                })
#    
#            # Log the error for debugging
#            print("Error:", e)
#    
#            exception_type = type(e).__name__
#            error_message = str(e)
#            return JsonResponse({
#                "success": False,
#                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                "message": "An error occurred while processing the request.",
#                "error": error_message
#            })
#    


    
    






    @csrf_exempt
    def get_transcript_small(self, request):
        try:
            audio_file = request.FILES.get('audio_file')
            if audio_file is None:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Audio file not found in the request."
                })

            # Read the audio file content as a byte stream
            audio_data = audio_file.read()

            model_name = "openai/whisper-large-v2"
            asr_pipeline = pipeline("automatic-speech-recognition", model=model_name)

            # Load the audio data using librosa to get the sampling rate and convert to NumPy ndarray
            audio_data, sr = librosa.load(BytesIO(audio_data), sr=16000, dtype=np.float32)  # Convert to NumPy ndarray

            # Transcribe the audio
            transcription = asr_pipeline(audio_data)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Speech recognition successful.",
                "transcription": transcription
            })

        except Exception as e:
            error_message = str(e)  # Capture the error message
            print(error_message)  # Print the error message for debugging
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing the request.",
                "error": error_message
            })


    # @csrf_exempt
    # def get_transcript_medium(self, request):
    #     try:
    #         audio_file = request.FILES.get('audio_file')
    #         if audio_file is None:
    #             return JsonResponse({
    #                 "success": False,
    #                 "status": status.HTTP_400_BAD_REQUEST,
    #                 "message": "Audio file not found in the request."
    #             })

    #         # Read the audio file content as a byte stream
    #         audio_data = audio_file.read()

    #         model_name = "openai/whisper-medium"
    #         asr_pipeline = pipeline("automatic-speech-recognition", model=model_name)

    #         # Load the audio data using librosa to get the sampling rate and convert to NumPy ndarray
    #         audio_data, sr = librosa.load(BytesIO(audio_data), sr=16000, dtype=np.float32)  # Convert to NumPy ndarray

    #         # Transcribe the audio
    #         transcription = asr_pipeline(audio_data)

    #         return JsonResponse({
    #             "success": True,
    #             "status": status.HTTP_200_OK,
    #             "message": "Speech recognition successful.",
    #             "transcription": transcription
    #         })

    #     except Exception as e:
    #         error_message = str(e)  # Capture the error message
    #         print(error_message)  # Print the error message for debugging
    #         return JsonResponse({
    #             "success": False,
    #             "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "message": "An error occurred while processing the request.",
    #             "error": error_message
    #         })
        


    @csrf_exempt
    def get_transcript_medium(self, request):
        try:
            audio_file = request.FILES.get('audio_file')
            if audio_file is None:
                return JsonResponse({
                    "success": False,
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Audio file not found in the request."
                })

            # Read the audio file content as a byte stream
            audio_data = audio_file.read()

            model_name = "openai/whisper-medium"
            asr_pipeline = pipeline("automatic-speech-recognition", model=model_name)

            # Split the audio into smaller segments (e.g., 5 minutes each)
            segment_duration_ms = 5 * 60 * 1000  # 5 minutes in milliseconds
            audio_segments = AudioSegment.from_file(BytesIO(audio_data), format="wav")
            segment_transcriptions = []

            for i in range(0, len(audio_segments), segment_duration_ms):
                segment = audio_segments[i:i+segment_duration_ms]

                # Convert the segment to bytes and load it using librosa
                segment_bytes = segment.export(format="wav").read()
                segment_audio, sr = librosa.load(BytesIO(segment_bytes), sr=16000, dtype=np.float32)  # Convert to NumPy ndarray

                # Process the audio using FFmpeg with increased analyzeduration and probesize
                cmd = [
                    settings.FFMPEG_BINARY,  # Path to the FFmpeg executable
                    "-analyzeduration", "2147483647",  # Set a large value for analyzeduration
                    "-probesize", "2147483647",  # Set a large value for probesize
                    "-f", "wav",  # Output format (assuming you want WAV)
                    "-",  # Output to stdout
                ]
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = process.communicate(input=segment_bytes)

                if process.returncode != 0:
                    error_message = f"Decoding failed. FFmpeg returned error code: {process.returncode}\n\nOutput from FFmpeg:\n\n{error.decode('utf-8')}"
                    raise Exception(error_message)

                # Transcribe the segment
                segment_transcription = asr_pipeline(segment_audio)
                segment_transcriptions.append(segment_transcription[0]['text'])

            # Combine the transcriptions of all segments
            full_transcription = " ".join(segment_transcriptions)

            return JsonResponse({
                "success": True,
                "status": status.HTTP_200_OK,
                "message": "Speech recognition successful.",
                "transcription": {
                    "text": full_transcription
                }
            })

        except Exception as e:
            error_message = str(e)  # Capture the error message
            print(error_message)  # Print the error message for debugging
            return JsonResponse({
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while processing the request.",
                "error": error_message
            })
