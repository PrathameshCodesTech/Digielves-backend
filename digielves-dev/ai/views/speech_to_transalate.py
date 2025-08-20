import deepspeech
import numpy as np
from pydub import AudioSegment
from io import BytesIO

def load_deepspeech_model(model_path):
    # Load the DeepSpeech model
    model = deepspeech.Model(model_path)
    return model

def translate_audio(audio_file_path):
    # Set the FFmpeg executable name
    AudioSegment.converter = "ffmpeg"

    # Initialize DeepSpeech model
    model_path = '/home/user/Desktop/Development/Backend/digielves-dev/ai/deepspeech-0.9.3-models.pbmm'
    model = load_deepspeech_model(model_path)

    # Process the local audio file using DeepSpeech
    with open(audio_file_path, 'rb') as local_audio_file:
        audio_data = local_audio_file.read()

        # Check if the file is in MP3 format and convert to WAV if needed
        if audio_file_path.lower().endswith('.mp3'):
            audio_data = AudioSegment.from_mp3(BytesIO(audio_data)).export(format="wav").read()

        # Convert audio data to numpy array
        numpy_data = np.frombuffer(audio_data, dtype=np.int16)

        # Perform speech-to-text using DeepSpeech
        text = model.stt(numpy_data)

    return text

a = translate_audio("/home/user/Desktop/Development/Backend/digielves-dev/ai/Dr. Mastakim Mazumdar 03.mp3")
print(a)

