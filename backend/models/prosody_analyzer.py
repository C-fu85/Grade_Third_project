import librosa
import numpy as np
from transformers import pipeline

# Load the model locally
MODEL_PATH = r"E:\code\Grade_Third_project\stutter_detection_model"  # 使用原始字符串避免反斜杠問題
pipe = pipeline("audio-classification", model=MODEL_PATH, device=0)

def convert_to_json_serializable(obj):
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    return obj

def analyze_prosody(audio_path, start_time=None, end_time=None, sample_rate=16000):
    try:
        duration = end_time - start_time if start_time is not None and end_time is not None else None
        audio, sr = librosa.load(audio_path, sr=sample_rate, offset=start_time or 0, duration=duration)

        if audio is None or len(audio) == 0:
            print(f"Error: Audio file {audio_path} could not be loaded or is empty.")
            return None

        # 計算持續時間（秒）
        duration = (end_time - start_time) if start_time is not None and end_time is not None else len(audio) / sr

        audio = librosa.util.normalize(audio)
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        return None

    try:
        pitch_values, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C6')
        )
        pitch_values = pitch_values[voiced_flag]
        pitch_values = pitch_values[(pitch_values > 80) & (pitch_values < 600)]

        pitch_mean = np.mean(pitch_values) if len(pitch_values) > 0 else 0
        pitch_variation = np.std(pitch_values) if len(pitch_values) > 0 else 0

        rms_energy = librosa.feature.rms(y=audio).flatten()
        energy_mean = np.mean(rms_energy)
        energy_variation = np.std(rms_energy)

        return convert_to_json_serializable({
            "Duration": duration,  # 添加 Duration
            "Pitch Mean": pitch_mean,
            "Pitch Variation": pitch_variation,
            "Energy Mean": energy_mean,
            "Energy Variation": energy_variation,
        })
    except Exception as e:
        print(f"Error during feature extraction: {e}")
        return None




def analyze_stuttering(segments, prosody_results, word_timestamps, audio_path):
    print(f"Starting stuttering analysis with {len(segments)} segments, {len(prosody_results)} prosody results, {len(word_timestamps)} word timestamps")
    print("Segments:", segments)
    print("Prosody Results:", prosody_results)
    print("Word Timestamps:", word_timestamps)

    if not segments or not prosody_results or len(segments) != len(prosody_results):
        print("Error: Mismatch between segments and prosody results or empty input")
        return []

    # 閾值設定
    STUTTER_REPETITION_THRESHOLD = 2  # 詞語重複閾值
    PAUSE_THRESHOLD = 1.5  # 語段間停頓閾值
    WORD_PAUSE_THRESHOLD = 0.25  # 單字間停頓閾值
    WORD_DURATION_THRESHOLD = 0.7  # 聲音拉長閾值
    INTERJECTION_ENERGY_THRESHOLD = 0.3  # 插入語能量閾值
    MODEL_CONFIDENCE_THRESHOLD = 0.7  # 模型預測置信度閾值
    INTERJECTIONS = {"嗯", "啊", "這個", "那個", "就是", "然後", "呃"}

    # 加載音頻文件
    audio, sr = librosa.load(audio_path, sr=16000)

    feedback = []
    for i, (segment, prosody) in enumerate(zip(segments, prosody_results)):
        print(f"Analyzing segment {i + 1}: {segment['text']}")
        if not prosody or "Duration" not in prosody:
            print(f"Skipping segment {i + 1} due to missing Duration: {prosody}")
            continue

        # 1. 模型預測結巴
        start_sample = int(segment["start"] * sr)
        end_sample = int(segment["end"] * sr)
        segment_audio = audio[start_sample:end_sample]
        model_results = pipe(segment_audio)
        print(f"Model results for segment {i + 1}: {model_results}")

        # 提取模型預測的各類結巴概率
        stutter_probs = {res["label"]: res["score"] for res in model_results}
        max_stutter_label = max(model_results, key=lambda x: x["score"])["label"]
        max_stutter_prob = stutter_probs[max_stutter_label]
        print(f"Max stutter label: {max_stutter_label}, Probability: {max_stutter_prob:.4f}")

        # 如果模型預測為 nonstutter，跳過此語段
 

        words = segment["text"].split()
        segment_feedback = []

        # 2. 數據分析：檢查任何結巴問題
        # 詞語重複檢測
        repetition_count = 1
        for j in range(1, len(words)):
            if words[j] == words[j-1]:
                repetition_count += 1
                if repetition_count >= STUTTER_REPETITION_THRESHOLD:
                    print(f"Repetition detected: '{words[j]}' repeated {repetition_count} times")
                    segment_feedback.append({
                        "type": "repetition",
                        "segment_index": i + 1,
                        "text": segment["text"],
                        "severity": "high" if max_stutter_prob > 0.9 else "medium",
                        "message": f"詞語重複: '{words[j]}' 重複 {repetition_count} 次。",
                        "start_time": segment["start"],
                        "end_time": segment["end"],
                        "confidence": max_stutter_prob,
                        "model_label": max_stutter_label
                    })
            else:
                repetition_count = 1

        # 單字級別分析
        segment_word_timestamps = [
            wt for wt in word_timestamps
            if wt["start"] >= segment["start"] and wt["end"] <= segment["end"]
        ]
        print(f"Word timestamps count: {len(segment_word_timestamps)}")

        for wt in segment_word_timestamps:
            word = wt["word"].strip()
            word_duration = wt["end"] - wt["start"]
            num_chars = len(word)
            avg_word_duration = word_duration / num_chars if num_chars > 1 else word_duration
            is_end_word = segment["text"].strip().endswith(word)
            if is_end_word:
                continue

            # 插入語檢測
            if word in INTERJECTIONS and prosody["Energy Variation"] > INTERJECTION_ENERGY_THRESHOLD:
                print(f"Interjection detected: '{word}'")
                segment_feedback.append({
                    "type": "interjection",
                    "segment_index": i + 1,
                    "text": segment["text"],
                    "severity": "high" if max_stutter_prob > 0.9 else "medium",
                    "message": f"插入語: '{word}' (持續時間 {word_duration:.1f} 秒)。",
                    "start_time": wt["start"],
                    "end_time": wt["end"],
                    "confidence": max_stutter_prob,
                    "model_label": max_stutter_label
                })

            # 聲音拉長檢測
            if avg_word_duration > WORD_DURATION_THRESHOLD:
                print(f"Word prolongation detected: '{word}' (avg duration per char: {avg_word_duration:.2f}s)")
                segment_feedback.append({
                    "type": "prolongation",
                    "segment_index": i + 1,
                    "text": segment["text"],
                    "severity": "high" if max_stutter_prob > 0.9 else "medium",
                    "message": f"聲音拉長: '{word}' 平均持續時間 {avg_word_duration:.1f} 秒/字元。",
                    "start_time": wt["start"],
                    "end_time": wt["end"],
                    "confidence": max_stutter_prob,
                    "model_label": max_stutter_label
                })

        # 單字間停頓檢測
        for j in range(1, len(segment_word_timestamps)):
            word_pause = segment_word_timestamps[j]["start"] - segment_word_timestamps[j-1]["end"]
            if word_pause > WORD_PAUSE_THRESHOLD:
                print(f"Word pause detected: {word_pause:.2f}s")
                segment_feedback.append({
                    "type": "pause",
                    "segment_index": i + 1,
                    "text": segment["text"],
                    "severity": "high" if max_stutter_prob > 0.9 else "medium",
                    "message": f"單字間停頓: '{segment_word_timestamps[j-1]['word']}' 和 '{segment_word_timestamps[j]['word']}' 間停頓 {word_pause:.1f} 秒。",
                    "start_time": segment_word_timestamps[j-1]["end"],
                    "end_time": segment_word_timestamps[j]["start"],
                    "confidence": max_stutter_prob,
                    "model_label": max_stutter_label
                })

        # 3. 結合邏輯：模型不是 nonstutter 且數據分析有任何問題
        if (max_stutter_prob > MODEL_CONFIDENCE_THRESHOLD and max_stutter_label != "repetition") or segment_feedback:
            print(f"Confirmed stutter in segment {i + 1}: Model label {max_stutter_label} (prob {max_stutter_prob:.4f}) with data analysis issues")
            feedback.extend(segment_feedback)
        else:
            print(f"Segment {i + 1} skipped: Either model prob < threshold or no data analysis issues detected")

    # 添加總結
    if feedback:
        feedback.append({
            "type": "summary",
            "stutter_issues": len(feedback),
            "total_segments": len(segments),
            "message": f"檢測到 {len(feedback)} 個結巴問題，共 {len(segments)} 個語段。"
        })
        print(f"Final feedback: {feedback}")

    return convert_to_json_serializable(feedback)
# import torch
# import torchaudio
# import torchaudio.transforms as T

# def analyze_prosody(audio_path, start_time=None, end_time=None, sample_rate=16000):
#     """
#     Analyze prosody features of an audio file using GPU with PyTorch.
#     """
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     # print(f"Using device: {device}")

#     try:
#         # Load the audio file with torchaudio (use GPU if available)
#         waveform, sr = torchaudio.load(audio_path)
#         waveform = waveform.to(device)

#         # Resample if necessary
#         if sr != sample_rate:
#             resampler = T.Resample(orig_freq=sr, new_freq=sample_rate).to(device)
#             waveform = resampler(waveform)
#             sr = sample_rate

#         # Trim to the specified segment if start_time and end_time are given
#         if start_time is not None and end_time is not None:
#             start_sample = int(start_time * sr)
#             end_sample = int(end_time * sr)
#             waveform = waveform[:, start_sample:end_sample]

#         # Normalize the audio
#         waveform = waveform / waveform.abs().max()

#         # Compute pitch using torchaudio's pitch detection (GPU accelerated)
#         pitch_transform = T.PitchShift(sample_rate=sr, n_steps=0).to(device)
#         pitch_values = pitch_transform(waveform).cpu().numpy().flatten()

#         # Filter pitch values for valid range
#         pitch_values = pitch_values[(pitch_values > 80) & (pitch_values < 600)]
#         pitch_mean = torch.tensor(pitch_values).mean().item() if len(pitch_values) > 0 else 0
#         pitch_variation = torch.tensor(pitch_values).std().item() if len(pitch_values) > 0 else 0

#         # Compute RMS energy
#         rms_transform = T.ComputeDeltas(order=0).to(device)
#         rms_energy = rms_transform(waveform).mean(dim=-1).cpu().numpy()
#         energy_mean = rms_energy.mean()
#         energy_variation = rms_energy.std()

#         return {
#             "Pitch Mean": pitch_mean,
#             "Pitch Variation": pitch_variation,
#             "Energy Mean": energy_mean,
#             "Energy Variation": energy_variation,
#         }

#     except Exception as e:
#         print(f"Error processing audio file {audio_path}: {e}")
#         return None