import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from pydub import AudioSegment

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Specify the language and model ID
LANG_ID = "zh-CN"
MODEL_ID = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"

def convert_to_wav(file_path):
    sound = AudioSegment.from_mp3(file_path)
    wav_path = file_path.replace(".mp3", ".wav")
    sound.export(wav_path, format="wav")
    return wav_path

# List of your own audio file paths
audio_files = [
    convert_to_wav(r"路過人間 郁可唯.mp3"),
    # Add more paths as needed
]

# Load the Wav2Vec2 processor and model
processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID)

# Function to process a single audio file
def process_audio(file_path):
    # Load the audio file and resample to 16kHz if needed
    speech_array, sampling_rate = librosa.load(file_path, sr=16_000)
    
    return speech_array

# Process each audio file and make predictions
for file_path in audio_files:
    # Convert audio file to the required format
    speech_array = process_audio(file_path)
    
    # Tokenize and prepare for model input
    inputs = processor(speech_array, sampling_rate=16_000, return_tensors="pt", padding=True)
    
    # Perform inference
    with torch.no_grad():
        logits = model(inputs.input_values, attention_mask=inputs.attention_mask).logits

    # Get the predicted token IDs and decode to text
    predicted_ids = torch.argmax(logits, dim=-1)
    predicted_sentence = processor.decode(predicted_ids[0])

    # Print the prediction
    print(f"Audio File: {file_path}")
    print("Prediction:", predicted_sentence)
    print("-" * 100)


