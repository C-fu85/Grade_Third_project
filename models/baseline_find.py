from prosody_analyzer import analyze_prosody
import numpy as np
from pydub import AudioSegment
import os
import sys


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

sys.stdout = Logger("results/baseline.txt")

# 指定 M4A 文件夹路径
male_audio_dir = r"E:\Downloads\Downloads\male_audio_files"
female_audio_dir = r"E:\Downloads\Downloads\female_audio_files"
male_audio_dir_wav = r"E:\Downloads\Downloads\male_audio_files_wav"
female_audio_dir_wav = r"E:\Downloads\Downloads\female_audio_files_wav"


def convert_m4a_to_wav(input_dir, output_dir):
    """
    將指定目錄中的 M4A 檔案批量轉換為 WAV 格式，並保存到輸出目錄。

    參數：
        input_dir (str): 包含 M4A 檔案的目錄。
        output_dir (str): 保存 WAV 檔案的目錄。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith(".m4a"):
            m4a_path = os.path.join(input_dir, file_name)
            wav_name = os.path.splitext(file_name)[0] + ".wav"
            wav_path = os.path.join(output_dir, wav_name)

            try:
                # 讀取 M4A 檔案
                audio = AudioSegment.from_file(m4a_path, format="m4a")
                # 匯出為 WAV 格式
                audio.export(wav_path, format="wav")
                print(f"Converted {m4a_path} to {wav_path}")
            except Exception as e:
                print(f"Error converting {m4a_path}: {e}")
convert_m4a_to_wav(male_audio_dir,male_audio_dir_wav)
convert_m4a_to_wav(female_audio_dir,female_audio_dir_wav)

# 获取 M4A 文件列表
male_audio_files = [os.path.join(male_audio_dir_wav, file) for file in os.listdir(male_audio_dir_wav) if file.endswith(".wav")]
female_audio_files = [os.path.join(female_audio_dir_wav, file) for file in os.listdir(female_audio_dir_wav) if file.endswith(".wav")]

male_features = []
female_features = []

# 假設 `male_audio_files` 和 `female_audio_files` 是已標記的音頻文件列表
for audio_path in male_audio_files:
    print("\n計算:",audio_path)
    features = analyze_prosody(audio_path)
    if features is not None:  # Only append if features are valid
        male_features.append(features)

for audio_path in female_audio_files:
    print("\n計算:",audio_path)
    features = analyze_prosody(audio_path)
    if features is not None:  # Only append if features are valid
        female_features.append(features)

def calculate_baseline(features):
    pitch_mean = np.mean([f['Pitch Mean'] for f in features])
    pitch_variation = np.mean([f['Pitch Variation'] for f in features])
    energy_mean = np.mean([f['Energy Mean'] for f in features])
    energy_variation = np.mean([f['Energy Variation'] for f in features])
    return {
        "Pitch Mean": pitch_mean,
        "Pitch Variation": pitch_variation,
        "Energy Mean": energy_mean,
        "Energy Variation": energy_variation,
    }

male_baseline = calculate_baseline(male_features)
female_baseline = calculate_baseline(female_features)

print("Male Baseline:", male_baseline)
print("\n")
print("Female Baseline:", female_baseline)