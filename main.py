import numpy as np
import os
import random
import sys
from models.cloud_and_transcription import download_file_from_cloud, extract_audio_from_video, transcribe_audio_to_sentences,convert_m4a_to_wav
from audio_emotion_classifier import predict, processor, model
from prosody_analyzer import analyze_prosody
from async_logger import async_logger


sys.stdout = async_logger("output.txt")

data_folder = "data"
sample_rate = 16000

project_root = os.path.dirname(os.path.abspath(__file__)) 
os.chdir(project_root)

def process_local_audio():
    file_paths = [os.path.join(data_folder, path) for path in os.listdir(data_folder) if path.endswith(".wav")]

    if file_paths:
        # 隨機挑一個音檔資料
        path = random.choice(file_paths)
        print(f"Selected file: {path}")

        print("Running Emotion Classifier...")
        emotion, score = predict(path, processor, model)
        print(f"Emotion: {emotion} \t Score: {score}")

        print("\nRunning Prosody Analysis...")
        prosody_features = analyze_prosody(path, sample_rate=sample_rate)

        # 如果array有多個element，將element的mean找出來然後將這個mean當成scalar value
        if prosody_features:
            for feature, value in prosody_features.items():
                if isinstance(value, (np.ndarray, list)):
                    value = value.item() if value.size == 1 else value.mean()
                print(f"{feature}: {value:.2f}")

            # 根據參數來提供建議
            # if prosody_features["Pitch Variation"] < 20:
            #    print("Feedback: Try to vary your pitch for a more engaging delivery.")
            # if prosody_features["Energy Mean"] < 0.01:
            #     print("Feedback: Increase your vocal energy for better presence.")

    else:
        print(f"No .wav files found in {data_folder}")

def process_speech_from_cloud(file_url):
    # 下載影片並提取音訊
    m4a_audio_path = 'data/audio_from_cloud.m4a'
    wav_audio_path = 'data/audio_from_cloud.wav'
    download_file_from_cloud(file_url, m4a_audio_path)
    convert_m4a_to_wav(m4a_audio_path, wav_audio_path)


    # 如果是影片，提取音訊
    # if m4a_audio_path.endswith('.mp4'):
    #     extract_audio_from_video(m4a_audio_path, 'audio_from_video.wav')
    #     m4a_audio_path = 'audio_from_video.wav'

    # 使用 Whisper 將音訊轉換為文本並分割成句子
    print("Running whisper to divide sentence...\n")
    sentences, segments = transcribe_audio_to_sentences(wav_audio_path)

    print("Running Emotion Classifier and Prosody Analysis...\n")
    
    for segment in segments:
        print(f"Analyzing Sentence: {segment['text']}")
        
        # 情感分析
        emotion, score = predict(wav_audio_path, processor, model, start_time=segment['start'], end_time=segment['end'])
        print(f"Emotion: {emotion} \t Score: {score}")
        
        # 韻律分析
        prosody_features = analyze_prosody(wav_audio_path, start_time=segment['start'], end_time=segment['end'])
        if prosody_features:
            for feature, value in prosody_features.items():
                print(f"{feature}: {value:.2f}")

# 測試：從本地資料夾分析音檔
# process_local_audio()

# 測試：從雲端下載影片並進行分析
file_url = "https://drive.google.com/uc?id=1ZjeYD6ceGylJtfTbP2BoGQg0nolzVUPv"  # 替換為實際的雲端文件連結
process_speech_from_cloud(file_url)
