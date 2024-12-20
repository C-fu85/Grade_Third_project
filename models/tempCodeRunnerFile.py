import os
import json

# 定義一個函數來擷取情緒和音高變化
def extract_emotions_and_pitch_variation(file_path):
    emotion_pitch_map = {}  # 用來存儲情緒和對應的音高變化

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        current_emotion = None  # 當前情緒

        for line in lines:
            if "Predicted Emotion:" in line:
                # 擷取情緒
                current_emotion = line.split("Predicted Emotion:")[1].split("\t")[0].strip()
                if current_emotion not in emotion_pitch_map:
                    emotion_pitch_map[current_emotion] = []  # 初始化情緒的音高變化列表
            if "Pitch Variation:" in line and current_emotion:
                # 擷取音高變化
                pitch_variation = line.split("Pitch Variation:")[1].strip()
                emotion_pitch_map[current_emotion].append(float(pitch_variation))

    return emotion_pitch_map

# 定義一個函數來將數據寫入檔案
def write_emotion_pitch_to_file(emotion_pitch_data, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for emotion, pitch_variations in emotion_pitch_data.items():
            pitch_variations_str = ', '.join(map(str, pitch_variations))  # 將音高變化轉為字串
            output_file.write(f"Emotion: {emotion}, Pitch Variations: [{pitch_variations_str}]\n")

# 使用函數
input_file_path = 'models/results/emotion_log.txt'
output_file_path = 'results/prosody_log.txt'

emotion_pitch_data = extract_emotions_and_pitch_variation(input_file_path)
write_emotion_pitch_to_file(emotion_pitch_data, output_file_path)

print(f"情緒和音高變化已寫入檔案: {output_file_path}")