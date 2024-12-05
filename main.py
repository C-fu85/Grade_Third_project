# main.py
import numpy as np
import os
import random
from audio_emotion_classifier import predict, processor, model
from prosody_analyzer import analyze_prosody

data_folder = "data"
sample_rate = 16000

project_root = os.path.dirname(os.path.abspath(__file__)) 
os.chdir(project_root)

file_paths = [os.path.join(data_folder, path) for path in os.listdir(data_folder) if path.endswith(".wav")]

if file_paths:
    # 隨機挑一個音檔資料，所以data裏只能放一個音儅。 要測試的話先把原先的test.wav替代掉。以後再改
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

        # 根據參數來提供建議, 目前先用不到。
        # if prosody_features["Pitch Variation"] < 20:
        #    print("Feedback: Try to vary your pitch for a more engaging delivery.")
        # if prosody_features["Energy Mean"] < 0.01:
        #     print("Feedback: Increase your vocal energy for better presence.")

else:
    print(f"No .wav files found in {data_folder}")
