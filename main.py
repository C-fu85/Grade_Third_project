import numpy as np
import os
import random
import sys
from audio_emotion_classifier import predict, processor, model
from prosody_analyzer import analyze_prosody

class Logger:
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger("output.txt")

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

else:
    print(f"No .wav files found in {data_folder}")
