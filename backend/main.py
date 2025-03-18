import numpy as np
import os
import random
import sys
import json
import hashlib
from datetime import datetime
from models.cloud_and_transcription import download_file_from_cloud, extract_audio_from_video, transcribe_audio_to_sentences, convert_m4a_to_wav
from models.audio_emotion_classifier import predict, processor, model
from models.prosody_analyzer import analyze_prosody, analyze_stuttering,convert_to_json_serializable
import requests
from flask import Flask, request, jsonify

class Logger:
    def __init__(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        try:
            self.terminal.write(message)
        except UnicodeEncodeError:
            self.terminal.write(message.encode('utf-8', errors='replace').decode('utf-8'))
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

class AudioAnalysisCache:
    def __init__(self, cache_file="cache/cache_data.json"):
        self.cache_file = cache_file
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self.cache_data = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        print(f"Cache file {self.cache_file} is empty, initializing with empty dict")
                        return {}
                    return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Failed to decode cache file {self.cache_file}: {str(e)}. Initializing with empty dict")
                return {}
            except Exception as e:
                print(f"Error reading cache file {self.cache_file}: {str(e)}. Initializing with empty dict")
                return {}
        print(f"Cache file {self.cache_file} does not exist, initializing with empty dict")
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)

    def _generate_cache_key(self, file_path, start_time=None, end_time=None):
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if start_time is not None and end_time is not None:
            return f"{file_hash}_{start_time}_{end_time}"
        return file_hash

    def get_cached_result(self, file_path, start_time=None, end_time=None):
        cache_key = self._generate_cache_key(file_path, start_time, end_time)
        cached_data = self.cache_data.get(cache_key)
        if cached_data:
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).days < 7:
                return cached_data["results"]
        return None

    def save_to_cache(self, file_path, results, start_time=None, end_time=None):
        cache_key = self._generate_cache_key(file_path, start_time, end_time)
        self.cache_data[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }
        self._save_cache()

def process_local_audio(cache=None):
    if cache is None:
        cache = AudioAnalysisCache()
    
    file_paths = [os.path.join(data_folder, path) for path in os.listdir(data_folder) if path.endswith(".wav")]
    if file_paths:
        path = random.choice(file_paths)
        print(f"Selected file: {path}")
        cached_results = cache.get_cached_result(path)
        if cached_results:
            print("Using cached results...")
            print_analysis_results(cached_results)
            return
        print("Running new analysis...")
        results = run_analysis(path)
        cache.save_to_cache(path, results)
        print_analysis_results(results)
    else:
        print(f"No .wav files found in {data_folder}")

def process_speech_from_cloud(file_url, cache=None):
    if cache is None:
        cache = AudioAnalysisCache()
    
    m4a_audio_path = 'data/audio_from_cloud.m4a'
    wav_audio_path = 'data/audio_from_cloud.wav'
    if not os.path.exists(wav_audio_path):
        if not os.path.exists(m4a_audio_path):
            print("Downloading from cloud...")
            download_file_from_cloud(file_url, m4a_audio_path)
        print("Converting M4A to WAV...")
        convert_m4a_to_wav(m4a_audio_path, wav_audio_path)

    print("Running Whisper to divide sentences...\n")
    sentences, segments = transcribe_audio_to_sentences(wav_audio_path)
    combined_segments = []
    for i in range(0, len(segments), 2):
        segment = {"text": segments[i]['text'], "start": segments[i]['start'], "end": segments[i]['end']}
        if i + 1 < len(segments):
            segment["text"] += f" {segments[i + 1]['text']}"
            segment["end"] = segments[i + 1]['end']
        combined_segments.append(segment)

    print("Running analysis on segments...\n")
    for segment in combined_segments:
        cached_results = cache.get_cached_result(wav_audio_path, start_time=segment['start'], end_time=segment['end'])
        if cached_results:
            print(f"Using cached results for: {segment['text']}")
            print_analysis_results(cached_results)
            continue
        print(f"Running new analysis for: {segment['text']}")
        results = run_analysis(wav_audio_path, start_time=segment['start'], end_time=segment['end'])
        results['text'] = segment['text']
        cache.save_to_cache(wav_audio_path, results, start_time=segment['start'], end_time=segment['end'])
        print_analysis_results(results)

def run_analysis(audio_path, start_time=None, end_time=None):
    results = {'emotion_analysis': {}, 'prosody_analysis': {}}
    emotion, score, emotion_scores = predict(audio_path, processor, model, start_time=start_time, end_time=end_time)
    results['emotion_analysis'] = {
        'primary_emotion': emotion,
        'primary_score': float(score),
        'all_scores': {k: float(v) for k, v in emotion_scores.items()}
    }
    prosody_features = analyze_prosody(audio_path, start_time=start_time, end_time=end_time)
    if prosody_features:
        results['prosody_analysis'] = {}
        for feature, value in prosody_features.items():
            if isinstance(value, (np.ndarray, list)):
                if isinstance(value, np.ndarray) and value.size == 1:
                    results['prosody_analysis'][feature] = float(value.item())
                else:
                    results['prosody_analysis'][feature + '_mean'] = float(np.mean(value))
                    results['prosody_analysis'][feature + '_values'] = [float(v) for v in value]
            elif isinstance(value, (int, float, np.number)):
                results['prosody_analysis'][feature] = float(value)
    return results

def print_analysis_results(results):
    if 'text' in results:
        print(f"Analyzing Sentence: {results['text']}")
    emotion_analysis = results['emotion_analysis']
    print(f"Emotion: {emotion_analysis['primary_emotion']} \t Score: {emotion_analysis['primary_score']}")
    print("All Emotion Scores:")
    for emotion, score in emotion_analysis['all_scores'].items():
        print(f"{emotion}: {score:.4f}")
    if 'prosody_analysis' in results:
        print("\nProsody Analysis:")
        for feature, value in results['prosody_analysis'].items():
            if isinstance(value, list):
                print(f"{feature}: Mean = {np.mean(value):.2f}")
            else:
                print(f"{feature}: {value:.2f}")
    print("\n")

def analyze_pitch_segments(cache, audio_path=None, cache_data=None, threshold=25, gender=None):
    """
    Analyze pitch segments with gender-aware thresholds.
    - threshold: Base threshold for low pitch variation (default 50 Hz).
    - gender: Optional 'male' or 'female' to adjust thresholds slightly (if provided).
    """
    if audio_path is None and cache_data is None:
        raise ValueError("Either audio_path or cache_data must be provided")

    # Adjust thresholds based on gender
    if gender == "male":
        base_threshold =  20  # Lowered to 30 Hz so 39 Hz isn’t flagged
        high_multiplier = 3.5  # ~75 Hz for "very high"
    elif gender == "female":
        base_threshold = 30  # Kept at 60 Hz per your current setup
        high_multiplier = 3.5  # ~150 Hz for "very high"
    else:
        base_threshold = threshold  # Default 50 Hz if no gender specified
        high_multiplier = 3.5  # ~125 Hz for "very high"

    # Load cache data
    if audio_path:
        base_hash = hashlib.md5(open(audio_path, 'rb').read()).hexdigest()
        if not os.path.exists(cache.cache_file):
            print(f"No cache file found: {cache.cache_file}")
            return []
        try:
            with open(cache.cache_file, "r", encoding='utf-8') as f:
                all_cached_data = json.load(f)
        except Exception as e:
            print(f"Error reading cache file: {str(e)}")
            return []
    elif cache_data:
        all_cached_data = cache_data
        base_hash = list(cache_data.keys())[0].split('_')[0]

    segments = []
    for key, cached_data in all_cached_data.items():
        if key.startswith(base_hash):
            results = cached_data.get("results", {})
            if "pitch_feedback" in results and results["pitch_feedback"]:
                pitch_entry = results["pitch_feedback"][0]
                segment_data = {
                    "text": pitch_entry["text"],
                    "pitch_variance": pitch_entry["Pitch Variation"],
                    "energy_mean": pitch_entry["Energy Mean"],
                    "duration": pitch_entry["Duration"],
                    "start_time": pitch_entry["start_time"],
                    "end_time": pitch_entry["end_time"]
                }
                segments.append(segment_data)

    if not segments:
        print(f"No valid segments found for audio: {audio_path or 'provided cache'}")
        return []

    feedback = []
    low_pitch_streak = 0
    for i, segment in enumerate(segments):
        if segment["pitch_variance"] is None:
            continue
        print(f"Segment {i + 1}: Text = '{segment['text']}', Pitch Variance = {segment['pitch_variance']:.2f} Hz")
        pitch_feedback = None
        if segment["pitch_variance"] < base_threshold:
            low_pitch_streak += 1
            # Adjust severity: "high" only if below half the threshold (e.g., 15 Hz for males)
            severity = "high" if segment["pitch_variance"] < base_threshold / 2 else "medium"
            pitch_feedback = {
                "segment_index": i + 1,
                "text": segment["text"],
                "pitch_variance": segment["pitch_variance"],
                "severity": severity,
                "message": f"Low pitch variation ({segment['pitch_variance']:.1f} Hz). Add more vocal variety.",
                "start_time": segment["start_time"],
                "end_time": segment["end_time"]
            }
        else:
            low_pitch_streak = 0
            if segment["pitch_variance"] > base_threshold * high_multiplier:  # e.g., > 75 Hz for males
                pitch_feedback = {
                    "segment_index": i + 1,
                    "text": segment["text"],
                    "pitch_variance": segment["pitch_variance"],
                    "severity": "medium",
                    "message": f"Very high pitch variation ({segment['pitch_variance']:.1f} Hz). Moderate for natural delivery.",
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"]
                }
        if pitch_feedback:
            feedback.append(pitch_feedback)
        if low_pitch_streak == 3:
            feedback.append({
                "segment_index": i - 1,
                "severity": "high",
                "streak": True,
                "message": "Multiple segments with low pitch variation. Incorporate more dynamics.",
                "start_time": segments[i - 2]["start_time"],  # 從前三個語段開始
                "end_time": segment["end_time"]
            })

    if feedback:
        avg_variance = np.mean([s["pitch_variance"] for s in segments if s["pitch_variance"] is not None])
        feedback.append({
            "type": "summary",
            "average_pitch_variance": avg_variance,
            "total_segments": len(segments),
            "segments_with_issues": len([f for f in feedback if not f.get("streak", False)]),
            "message": f"Average pitch variance: {avg_variance:.1f} Hz. Issues in {len([f for f in feedback if not f.get('streak', False)])}/{len(segments)} segments."
        })
    return feedback

def print_pitch_feedback(feedback):
    for item in feedback:
        if item.get('type') == 'summary':
            print("\nSummary:")
            print(item['message'])
            continue
        severity_marker = "❗️" if item['severity'] == 'high' else "ℹ️"
        if item.get('streak', False):
            print(f"\n{severity_marker} {item['message']}")
        else:
            print(f"\nSegment {item['segment_index']}:")
            print(f"Text: {item.get('text', 'N/A')}")
            print(f"{severity_marker} {item['message']}")

def send_to_api(endpoint, data):
    try:
        response = requests.post(endpoint, json=data)
        response.raise_for_status()
        print(f"Successfully sent data to {endpoint}. Response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data to {endpoint}: {str(e)}")

def process_speech_from_file(file_path, cache=None, gender=None):
    if cache is None:
        cache = AudioAnalysisCache()

    wav_audio_path = "data/temp_audio.wav"
    try:
        if file_path.endswith(".m4a"):
            print(f"Converting {file_path} to WAV...")
            convert_m4a_to_wav(file_path, wav_audio_path)
        else:
            wav_audio_path = file_path
            print(f"Using {file_path} directly as WAV file")

        print(f"File size: {os.path.getsize(wav_audio_path)} bytes")
        print("Running Whisper to divide sentences...\n")
        sentences, segments, word_timestamps = transcribe_audio_to_sentences(wav_audio_path)
        if not segments:
            raise ValueError("No segments found in audio transcription")
        print(f"Transcription completed: {len(segments)} segments")

        combined_segments = segments
        print(f"Processing {len(combined_segments)} individual segments")

        # 儲存所有語段的文字和時間
        transcriptions = [
            {
                "segment_index": i + 1,
                "text": segment["text"],
                "start_time": segment["start"],
                "end_time": segment["end"]
            }
            for i, segment in enumerate(combined_segments)
        ]

        analysis_results = {}
        prosody_results = []

        # 逐段處理快取和分析
        for i, segment in enumerate(combined_segments):
            cache_key = cache._generate_cache_key(wav_audio_path, segment["start"], segment["end"])
            cached_results = cache.get_cached_result(wav_audio_path, segment["start"], segment["end"])
            if cached_results:
                print(f"Using cached results for segment {segment['start']}-{segment['end']}")
                if "pitch_feedback" not in cached_results or not isinstance(cached_results["pitch_feedback"], list) or not cached_results["pitch_feedback"]:
                    print(f"Warning: Invalid cached results for {cache_key}, skipping: {cached_results}")
                    continue
                analysis_results[cache_key] = {"timestamp": datetime.now().isoformat(), "results": cached_results}
                prosody_results.append(cached_results["pitch_feedback"][0])
            else:
                print(f"Running new analysis for segment {segment['start']}-{segment['end']}: {segment['text']}")
                prosody = analyze_prosody(wav_audio_path, start_time=segment["start"], end_time=segment["end"])
                print(f"Prosody for '{segment['text']}': {prosody}")
                if prosody and "Pitch Variation" in prosody:
                    prosody_results.append(prosody)
                    pitch_entry = {
                        "segment_index": i + 1,
                        "text": segment["text"],
                        "Duration": prosody.get("Duration", 0),
                        "Pitch Mean": prosody.get("Pitch Mean", 0),
                        "Pitch Variation": prosody.get("Pitch Variation", 0),
                        "Energy Mean": prosody.get("Energy Mean", 0),
                        "Energy Variation": prosody.get("Energy Variation", 0),
                        "start_time": segment["start"],
                        "end_time": segment["end"]
                    }
                    results = {
                        "text": segment["text"],
                        "pitch_feedback": [pitch_entry]
                    }
                    cache.save_to_cache(wav_audio_path, results, segment["start"], segment["end"])
                    analysis_results[cache_key] = {"timestamp": datetime.now().isoformat(), "results": results}
                else:
                    print(f"Warning: No valid prosody data for segment {segment['start']}-{segment['end']}")

        # 運行結巴分析
        stutter_feedback = analyze_stuttering(combined_segments, prosody_results, word_timestamps) if prosody_results else []
        print(f"Stutter feedback: {stutter_feedback}")

        # 使用 analyze_pitch_segments 生成音高反饋
        pitch_feedback = analyze_pitch_segments(cache, audio_path=wav_audio_path, threshold=25, gender=gender)
        print(f"pitch feedback: {pitch_feedback}")

        # 組合最終反饋
        combined_feedback = pitch_feedback + stutter_feedback

        # 清理臨時檔案
        if wav_audio_path != file_path and  os.path.exists(wav_audio_path):
            os.remove(wav_audio_path)
            print(f"Cleaned up temporary file: {wav_audio_path}")

        # 返回兩部分數據
        return {
            "transcriptions": convert_to_json_serializable(transcriptions),
            "feedback": convert_to_json_serializable(combined_feedback)
        }
    except Exception as e:
        print(f"Error in process_speech_from_file: {str(e)}")
        raise

def create_flask_app():
    app = Flask(__name__)

    @app.route('/api/transcribe', methods=['POST'])
    def transcribe_audio():
        try:
            if "file" not in request.files:
                print("No file provided in request")
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files["file"]
            gender = request.args.get("gender")
            print(f"Gender from form data: {gender}")

            file_ext = os.path.splitext(file.filename)[1]
            temp_filename = f"uploaded_{hashlib.md5(file.filename.encode('utf-8')).hexdigest()}{file_ext}"
            temp_path = os.path.join("data", temp_filename)
            
            file.save(temp_path)
            print(f"File saved: {temp_path}, size: {os.path.getsize(temp_path)} bytes")

            cache = AudioAnalysisCache()
            result = process_speech_from_file(temp_path, cache, gender=gender)
            audio_path = "data/temp_audio.wav" if temp_path.endswith(".m4a") else temp_path
            
            print(f"Processing completed: {len(result['feedback'])} feedback items, {len(result['transcriptions'])} transcriptions")

            return jsonify({
                "transcriptions": result["transcriptions"],
                "feedback": result["feedback"]
            })
        except Exception as e:
            print(f"Error in /api/transcribe: {str(e)}")
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Cleaned up: {temp_path}")
            if 'audio_path' in locals() and audio_path != temp_path and os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up: {audio_path}")
        
    @app.route('/api/analyze', methods=['POST'])
    def analyze_audio():
        try:
            data = request.get_json()
            cache = AudioAnalysisCache()
            if 'cache_data' in data:
                pitch_feedback = analyze_pitch_segments(cache, cache_data=data['cache_data'], threshold=20)
                enhanced_feedback = []
                for item in pitch_feedback:
                    if item.get('type') == 'summary':
                        enhanced_feedback.append(item)
                        continue
                    segment_index = item['segment_index'] - 1
                    segment_key = list(data['cache_data'].keys())[segment_index]
                    _, start_time, end_time = segment_key.split('_')
                    item_with_time = item.copy()
                    item_with_time['start_time'] = float(start_time)
                    item_with_time['end_time'] = float(end_time)
                    enhanced_feedback.append(item_with_time)
                return jsonify({"feedback": enhanced_feedback})
            elif 'audio_path' in data:
                pitch_feedback = analyze_pitch_segments(cache, audio_path=data['audio_path'], threshold=20)
                enhanced_feedback = []
                for item in pitch_feedback:
                    if item.get('type') == 'summary':
                        enhanced_feedback.append(item)
                        continue
                    segment_index = item['segment_index'] - 1
                    segment_key = [k for k in cache.cache_data.keys() if k.startswith(hashlib.md5(open(data['audio_path'], 'rb').read()).hexdigest())][segment_index]
                    _, start_time, end_time = segment_key.split('_')
                    item_with_time = item.copy()
                    item_with_time['start_time'] = float(start_time)
                    item_with_time['end_time'] = float(end_time)
                    enhanced_feedback.append(item_with_time)
                return jsonify({"feedback": enhanced_feedback})
            return jsonify({"error": "Invalid request"}), 400
        except Exception as e:
            print(f"Error in /api/analyze: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return app

# 以下是你原有的其他函數，未列出但保持不變：
# process_local_audio, process_speech_from_cloud, run_analysis, print_analysis_results,
# analyze_pitch_segments, print_pitch_feedback, send_to_api

if __name__ == "__main__":
    sys.stdout = Logger("./results/two_sentences_output.txt")
    data_folder = "data"
    sample_rate = 16000
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    os.makedirs('data', exist_ok=True)
    os.makedirs('cache', exist_ok=True)

    try:
        cache = AudioAnalysisCache("cache/cache_data.json")
        print("Cache initialized successfully")
    except Exception as e:
        print(f"Failed to initialize cache: {str(e)}. Continuing with empty cache")
        cache = AudioAnalysisCache("cache/cache_data.json")

    import argparse
    parser = argparse.ArgumentParser(description="Audio Analysis Script")
    parser.add_argument("--server", action="store_true", help="Run as Flask server")
    args = parser.parse_args()

    if args.server:
        app = create_flask_app()
        app.run(host='0.0.0.0', port=5000)


    # Process speech from the cloud
    # file_url = "https://drive.google.com/uc?id=1ZjeYD6ceGylJtfTbP2BoGQg0nolzVUPv"
    # process_speech_from_cloud(file_url, cache)

    # # Analyze pitch variance and provide feedback
    # print("\nAnalyzing pitch patterns across segments...")
    # pitch_feedback = analyze_pitch_segments(cache, "data/audio_from_cloud.wav", threshold=20)
    # print_pitch_feedback(pitch_feedback)