import numpy as np
import os
import random
import sys
from cloud_and_transcription import download_file_from_cloud, extract_audio_from_video, transcribe_audio_to_sentences,convert_m4a_to_wav
from audio_emotion_classifier import predict, processor, model
from prosody_analyzer import analyze_prosody
import librosa

class Logger:
    def __init__(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger("results/emotion_log.txt")

data_folder_1 = r"E:\Downloads\Downloads\female_audio_files_wav"
data_folder_2 = r"E:\Downloads\Downloads\male_audio_files_wav"
sample_rate = 16000

project_root = os.path.dirname(os.path.abspath(__file__)) 
os.chdir(project_root)

def process_local_audio():
    # 打印路徑以進行調試
    print(f"Data folder 1 path: {data_folder_1}")
    print(f"Data folder 2 path: {data_folder_2}")

    # 合併兩個資料夾的檔案路徑
    file_paths = []
    for data_folder in [data_folder_1, data_folder_2]:
        file_paths.extend([os.path.join(data_folder, path) for path in os.listdir(data_folder) if path.endswith(".wav")])

    # 開啟 prosody_log.txt 以寫入
    with open("results/prosody_log.txt", "w", encoding="utf-8") as log_file:
        emotion_data = {}  # 用於儲存每種情緒的音高均值和變異

        if file_paths:
            for path in file_paths:  # 新增迴圈以處理每個檔案
                print(f"Selected file: {path}")
                
                # 使用 Whisper 將音訊轉換為文本並分割成句子
                print("Running whisper to divide sentence...\n")
                sentences, segments = transcribe_audio_to_sentences(path)

                print("Running Emotion Classifier and Prosody Analysis...\n")

                # 分析合併後的句子
                for segment in segments:
                    print(f"Analyzing Sentence: {segment['text']}")
                    print(f"Start Time: {segment['start']}, End Time: {segment['end']}")
                    # 情感分析
                    emotion, score, emotion_scores = predict(
                        path, processor, model,
                        start_time=segment['start'], end_time=segment['end']
                    )
                    print(f"Predicted Emotion: {emotion} \t Score: {score}")
                    
                    # 韻律分析
                    try:
                        prosody_features = analyze_prosody(
                            path, start_time=segment['start'], end_time=segment['end']
                        )
                        if prosody_features:
                            pitch_mean = prosody_features.get('pitch_mean', None)
                            pitch_variation = prosody_features.get('pitch_variation', None)

                            # 將音高均值和變異加入對應情緒的陣列
                            if emotion not in emotion_data:
                                emotion_data[emotion] = {'pitch_means': [], 'pitch_variations': []}
                            
                            emotion_data[emotion]['pitch_means'].append(pitch_mean)
                            emotion_data[emotion]['pitch_variations'].append(pitch_variation)

                            for feature, value in prosody_features.items():
                                print(f"{feature}: {value:.2f}")
                    except Exception as e:
                        print(f"Error analyzing prosody for segment: {segment['text']}. Error: {e}")
                        continue  # 繼續處理下一個段落
                    print("\n")

            # 將每種情緒的音高均值、變異和時間寫入文件
            for emotion, data in emotion_data.items():
                log_file.write(f"Emotion: {emotion}, Pitch Means: {data['pitch_means']}, Pitch Variations: {data['pitch_variations']}\n")

        else:
            print(f"No .wav files found in the specified folders.")

def process_speech_from_cloud(file_url):
    # 下載影片並提取音訊
    m4a_audio_path = 'data/audio_from_cloud.m4a'
    wav_audio_path = 'data/audio_from_cloud.wav'
    download_file_from_cloud(file_url, m4a_audio_path)
    convert_m4a_to_wav(m4a_audio_path, wav_audio_path)


    # 如果是影片，提取音訊.
    # if m4a_audio_path.endswith('.mp4'):
    #     extract_audio_from_video(m4a_audio_path, 'audio_from_video.wav')
    #     m4a_audio_path = 'audio_from_video.wav'

    # 使用 Whisper 將音訊轉換為文本並分割成句子
    print("Running whisper to divide sentence...\n")
    sentences, segments = transcribe_audio_to_sentences(wav_audio_path)

    print("Running Emotion Classifier and Prosody Analysis...\n")

    # 修改後的句子分析邏輯
    combined_segments = []
    for i in range(0, len(segments), 2):
        # 合併當前句子和下一句子
        text = segments[i]['text']
        start_time = segments[i]['start']
        end_time = segments[i]['end']

        if i + 1 < len(segments):
            text += f" {segments[i + 1]['text']}"
            end_time = segments[i + 1]['end']

        combined_segments.append({
            "text": text.strip(),
            "start": start_time,
            "end": end_time
        })

    # 分析合併後的句子
    for segment in combined_segments:
        print(f"Analyzing Sentence: {segment['text']}")
        
        # 情感分析
        emotion, score, emotion_scores = predict(
            wav_audio_path, processor, model,
            start_time=segment['start'], end_time=segment['end']
        )
        print(f"Emotion: {emotion} \t Score: {score}")
        
        print("All Emotion Scores:")
        for emo, emo_score in emotion_scores.items():
            print(f"{emo}: {emo_score:.4f}")
        
        # 韻律分析
        prosody_features = analyze_prosody(
            wav_audio_path, start_time=segment['start'], end_time=segment['end']
        )
        if prosody_features:
            for feature, value in prosody_features.items():
                print(f"{feature}: {value:.2f}")
        print("\n")

    
    # for segment in segments:
    #     print(f"Analyzing Sentence: {segment['text']}")
        
    #     # 情感分析
    #     emotion, score, emotion_scores = predict(wav_audio_path, processor, model, start_time=segment['start'], end_time=segment['end'])
    #     print(f"Emotion: {emotion} \t Score: {score}")
        
    #     print("All Emotion Scores:")
    #     for emo, emo_score in emotion_scores.items():
    #         print(f"{emo}: {emo_score:.4f}")
    #     # 韻律分析
    #     prosody_features = analyze_prosody(wav_audio_path, start_time=segment['start'], end_time=segment['end'])
    #     if prosody_features:
    #         for feature, value in prosody_features.items():
    #             print(f"{feature}: {value:.2f}")




# 測試：從本地資料夾分析音檔
process_local_audio()

# 測試：從雲端下載影片並進行分析
# file_url = "https://drive.google.com/uc?id=1ZjeYD6ceGylJtfTbP2BoGQg0nolzVUPv"  # 替換為實際的雲端文件連結
# process_speech_from_cloud(file_url)
