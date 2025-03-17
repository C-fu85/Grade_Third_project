from moviepy.editor import VideoFileClip
import librosa
import numpy as np
import json
import whisper
import os

# 從影片提取音頻（僅用於影片檔案）
def extract_audio_from_video(video_path, output_audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(output_audio_path, codec='pcm_s16le')

# 語音轉文字
def transcribe_audio_to_sentences(audio_path, device='cuda'):
    try:
        model = whisper.load_model("medium").to(device)
        result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
        return result['segments']
    except Exception as e:
        print(f"Error in transcribe_audio_to_sentences: {str(e)}")
        raise

# 分析單字語音特徵
def analyze_word_prosody(audio_path, start_time, end_time, sample_rate=16000):
    try:
        duration = end_time - start_time
        audio, sr = librosa.load(audio_path, sr=sample_rate, offset=start_time, duration=duration)
        if len(audio) == 0:
            return None
        audio = librosa.util.normalize(audio)
        
        pitch_values, voiced_flag, _ = librosa.pyin(
            audio, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6')
        )
        pitch_values = pitch_values[voiced_flag]
        pitch_values = pitch_values[(pitch_values > 80) & (pitch_values < 600)]

        pitch_mean = np.mean(pitch_values) if len(pitch_values) > 0 else 0
        rms_energy = librosa.feature.rms(y=audio).flatten()
        energy_mean = np.mean(rms_energy)

        return {
            "Duration": duration,
            "Pitch Mean": pitch_mean,
            "Energy Mean": energy_mean
        }
    except Exception as e:
        print(f"Error in analyze_word_prosody: {e}")
        return None

# 儲存單段結果到 JSON
def save_segment_to_json(output_dir, output_file, data, segment_text):
    try:
        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, output_file)
        result = {
            "sentence": segment_text,
            "words": data
        }
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(data)} words for '{segment_text}' to '{os.path.abspath(full_path)}'.")
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")

# 處理單一句子的結巴標記
def mark_stutter_in_sentence(audio_path, segment):
    sentence_text = segment['text'].strip()
    print(f"\nProcessing sentence: '{sentence_text}'")
    print(f"Time: {segment['start']}s - {segment['end']}s")
    
    while True:
        choice = input("Does this sentence contain stuttering? (y/n/r to reback/i to ignore): ").strip().lower()
        if choice in ['y', 'n', 'r', 'i']:
            break
        print("Please enter 'y', 'n', 'r', or 'i'")

    if choice == 'r':
        return "reback"
    if choice == 'i':
        marked_words = []
        for word in segment.get("words", []):
            marked_words.append({
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "is_stutter": None,
                "stutter_type": "ignored"
            })
        print(f"Sentence '{sentence_text}' marked as ignored.")
        return marked_words

    marked_words = []
    if choice == 'n':
        for word in segment.get("words", []):
            marked_words.append({
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "is_stutter": False,
                "stutter_type": ""
            })
        return marked_words

    print("\nChecking each word in the sentence:")
    i = 0
    while i < len(segment.get("words", [])):
        word = segment["words"][i]
        prosody = analyze_word_prosody(audio_path, word["start"], word["end"])
        if not prosody:
            print(f"Skipping word '{word['word']}' due to missing prosody data")
            i += 1
            continue

        print(f"\nWord {i + 1}: '{word['word']}'")
        print(f"Time: {word['start']}s - {word['end']}s")
        print(f"Duration: {prosody['Duration']:.2f}s")
        
        if prosody["Duration"] > 0.7:
            print(f"Possible prolongation: Duration = {prosody['Duration']:.2f}s")
        if i > 0:
            pause_duration = word["start"] - segment["words"][i-1]["end"]
            if pause_duration > 0.25:
                print(f"Possible pause before word: {pause_duration:.2f}s")
        if i > 0 and word["word"] == segment["words"][i-1]["word"]:
            print(f"Possible repetition: Same as previous word")

        while True:
            choice = input("Is this word stuttered? (y/n/r to reback/i to ignore): ").strip().lower()
            if choice in ['y', 'n', 'r', 'i']:
                break
            print("Please enter 'y', 'n', 'r', or 'i'")

        if choice == 'r':
            if i > 0:
                i -= 1
                marked_words.pop()
                print(f"Reback to previous word: '{segment['words'][i]['word']}'")
            else:
                print("At the first word, reback to sentence level.")
                return "reback"
            continue
        elif choice == 'i':
            marked_words.append({
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "is_stutter": None,
                "stutter_type": "ignored"
            })
            print(f"Word '{word['word']}' marked as ignored.")
            i += 1
            continue

        stutter_type = ""
        if choice == 'y':
            stutter_type = input("Enter stutter type (e.g., repetition, prolongation, pause): ").strip()

        marked_words.append({
            "word": word["word"],
            "start": word["start"],
            "end": word["end"],
            "is_stutter": choice == 'y',
            "stutter_type": stutter_type
        })
        i += 1

    return marked_words

# 主流程：逐句處理音頻並儲存到指定目錄
def process_audio_for_stutter_marking(audio_path, device='cuda'):
    print(f"Transcribing audio from {audio_path}...")
    segments = transcribe_audio_to_sentences(audio_path, device)
    
    # 從音檔路徑提取主體名稱（去掉路徑和副檔名）
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]  # 例如 "male01"
    
    # 指定儲存目錄
    output_dir = "backend/data/mark"
    
    all_marked_results = []
    print("\nStarting sentence-by-sentence stutter marking...")
    
    i = 0
    serial_number = 1  # 流水號從 001 開始
    while i < len(segments):
        result = mark_stutter_in_sentence(audio_path, segments[i])
        if result == "reback" and i > 0:
            i -= 1
            if all_marked_results:
                last_sentence_end = segments[i]["end"]
                all_marked_results = [r for r in all_marked_results if r["end"] <= last_sentence_end]
                serial_number -= 1  # 回退時減少流水號
            print(f"Reback to previous sentence: '{segments[i]['text'].strip()}'")
        else:
            if result != "reback":
                all_marked_results.extend(result)
                # 為當前句子生成帶音檔名稱的獨立 JSON 檔案
                output_file = f"{audio_name}_stutter_marking_{serial_number:03d}.json"
                save_segment_to_json(output_dir, output_file, result, segments[i]['text'].strip())
                serial_number += 1
            i += 1

    print("Stutter marking completed.")

    # 顯示總覽
    print("\nFinal Results:")
    for item in all_marked_results:
        if item["is_stutter"] is True:
            print(f"Stutter detected - Word: '{item['word']}' at {item['start']}s - {item['end']}s, Type: {item['stutter_type']}")
        elif item["is_stutter"] is None:
            print(f"Ignored - Word: '{item['word']}' at {item['start']}s - {item['end']}s")
    
    return all_marked_results

# 測試範例
if __name__ == "__main__":
    audio_path = "backend/data/male01.wav"  # 更新音檔路徑
    results = process_audio_for_stutter_marking(audio_path)