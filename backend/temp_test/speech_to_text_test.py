
#r"C:\Users\fu\Downloads\路過人間 郁可唯.mp3"
import whisper
import librosa
import numpy as np
import matplotlib.pyplot as plt  # 確保這一行在代碼中
import sys
import io
from pyAudioAnalysis import audioTrainTest as aT

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 載入 Whisper 模型
model = whisper.load_model("small")

# 載入音頻文件
audio_path = "..\大三專題\路過人間 郁可唯.mp3"  # 更改為音頻文件路徑

# 轉錄語音
result = model.transcribe(audio_path)

# 計算語速 (每分鐘單詞數)
total_words = 0
total_duration = 0

# 顯示轉錄結果及時間戳
for segment in result['segments']:
    print(f"Text: {segment['text']}")
    print(f"Start time: {segment['start']}s, End time: {segment['end']}s")
    start_time = segment['start']
    end_time = segment['end']
    segment_duration = end_time - start_time
    
    # 計算該片段的單詞數
    segment_word_count = len(segment['text'])  # 計算字數
    
    # 累加總單詞數和總持續時間
    total_words += segment_word_count
    total_duration += segment_duration
    print(f"Total Words: {total_words}  Total Duration: {total_duration}s\n")

# 計算整體 WPM
overall_wpm = (total_words / total_duration) * 60 if total_duration > 0 else 0
print(f"Overall Words per minute (WPM): {overall_wpm}")

# 使用Librosa分析音頻
y, sr = librosa.load(audio_path, sr=None)

# 計算音頻的能量 (Energy)
frame_length = 1024
hop_length = 512
energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)

# 計算停頓（能量小於閾值的區域）
threshold = 0.02  # 設定閾值來檢測靜音
silent_frames = np.where(energy < threshold)[1]

# 顯示能量圖與停頓區域
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(energy[0], label='Energy')
plt.axhline(y=threshold, color='r', linestyle='--', label='Energy Threshold')
plt.legend()
plt.title("Energy vs. Threshold")
plt.xlabel("Frames")
plt.ylabel("Energy")

plt.subplot(2, 1, 2)
plt.plot(y)
plt.scatter(silent_frames * hop_length, y[silent_frames * hop_length], color='red', label="Pause")
plt.legend()
plt.title("Audio Signal with Pauses")
plt.xlabel("Samples")
plt.ylabel("Amplitude")

plt.tight_layout()
plt.show()



    






