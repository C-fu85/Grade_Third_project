import numpy as np
import os
import random
import sys
import json
import hashlib
from datetime import datetime
from models.cloud_and_transcription import download_file_from_cloud, extract_audio_from_video, transcribe_audio_to_sentences, convert_m4a_to_wav
from models.audio_emotion_classifier import predict, processor, model
from models.prosody_analyzer import analyze_prosody

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

class AudioAnalysisCache:
    def __init__(self, cache_file="cache/cache_data.json"):
        self.cache_file = cache_file
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self.cache_data = self._load_cache()

    def _load_cache(self):
        """Load the entire cache file into memory."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save the entire cache file from memory."""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)

    def _generate_cache_key(self, file_path, start_time=None, end_time=None):
        """Generate a unique cache key based on file content and segment times."""
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        if start_time is not None and end_time is not None:
            return f"{file_hash}_{start_time}_{end_time}"
        return file_hash

    def get_cached_result(self, file_path, start_time=None, end_time=None):
        """Retrieve cached result for a specific key."""
        cache_key = self._generate_cache_key(file_path, start_time, end_time)
        cached_data = self.cache_data.get(cache_key)
        if cached_data:
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if (datetime.now() - cache_time).days < 7:  # Check cache validity
                return cached_data["results"]
        return None

    def save_to_cache(self, file_path, results, start_time=None, end_time=None):
        """Save a result to the cache."""
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

        # Check cache first
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

    # Download and process the audio file if necessary
    if not os.path.exists(wav_audio_path):
        if not os.path.exists(m4a_audio_path):
            print("Downloading from cloud...")
            download_file_from_cloud(file_url, m4a_audio_path)
        
        print("Converting M4A to WAV...")
        convert_m4a_to_wav(m4a_audio_path, wav_audio_path)

    print("Running Whisper to divide sentences...\n")
    sentences, segments = transcribe_audio_to_sentences(wav_audio_path)

    # Process segments in pairs
    combined_segments = []
    for i in range(0, len(segments), 2):
        segment = {
            "text": segments[i]['text'],
            "start": segments[i]['start'],
            "end": segments[i]['end']
        }
        
        if i + 1 < len(segments):
            segment["text"] += f" {segments[i + 1]['text']}"
            segment["end"] = segments[i + 1]['end']
        
        combined_segments.append(segment)

    # Analyze each combined segment with caching
    print("Running analysis on segments...\n")
    for segment in combined_segments:
        cached_results = cache.get_cached_result(
            wav_audio_path, 
            start_time=segment['start'], 
            end_time=segment['end']
        )
        
        if cached_results:
            print(f"Using cached results for: {segment['text']}")
            print_analysis_results(cached_results)
            continue

        print(f"Running new analysis for: {segment['text']}")
        results = run_analysis(
            wav_audio_path,
            start_time=segment['start'],
            end_time=segment['end']
        )
        results['text'] = segment['text']
        cache.save_to_cache(
            wav_audio_path, 
            results,
            start_time=segment['start'],
            end_time=segment['end']
        )
        print_analysis_results(results)

def run_analysis(audio_path, start_time=None, end_time=None):
    results = {'emotion_analysis': {}, 'prosody_analysis': {}}
    
    # Emotion analysis
    emotion, score, emotion_scores = predict(
        audio_path, processor, model,
        start_time=start_time, end_time=end_time
    )
    results['emotion_analysis'] = {
        'primary_emotion': emotion,
        'primary_score': float(score),
        'all_scores': {k: float(v) for k, v in emotion_scores.items()}
    }
    
    # Prosody analysis
    prosody_features = analyze_prosody(
        audio_path,
        start_time=start_time,
        end_time=end_time
    )
    if prosody_features:
        # Ensure all numpy values are converted to native Python floats
        results['prosody_analysis'] = {}
        for feature, value in prosody_features.items():
            if isinstance(value, (np.ndarray, list)):
                # Handle both single values and arrays
                if isinstance(value, np.ndarray) and value.size == 1:
                    results['prosody_analysis'][feature] = float(value.item())
                else:
                    # For arrays, store both mean and raw values
                    results['prosody_analysis'][feature + '_mean'] = float(np.mean(value))
                    results['prosody_analysis'][feature + '_values'] = [float(v) for v in value]
            elif isinstance(value, (int, float, np.number)):
                # Handle scalar numeric values
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

def analyze_pitch_segments(cache, audio_path, threshold=20):
    """
    Analyze pitch variance across segments with more context-aware grouping.
    """
    base_hash = hashlib.md5(open(audio_path, 'rb').read()).hexdigest()

    if not os.path.exists(cache.cache_file):
        print(f"No cache file found: {cache.cache_file}")
        return []

    with open(cache.cache_file, 'r', encoding='utf-8') as f:
        all_cached_data = json.load(f)

    segments = []
    for key, cached_data in all_cached_data.items():
        if key.startswith(base_hash):
            results = cached_data.get("results", {})
            if "prosody_analysis" in results and "text" in results:
                # Adapt to new prosody data structure
                pitch_variance = results["prosody_analysis"].get("Pitch Variation_mean",
                               results["prosody_analysis"].get("Pitch Variation"))  # fallback for old cache entries
                
                segment_data = {
                    "text": results["text"],
                    "pitch_variance": pitch_variance,
                    "energy_mean": results["prosody_analysis"].get("Energy Mean_mean",
                                 results["prosody_analysis"].get("Energy Mean")),
                    "duration": results["prosody_analysis"].get("Duration_mean",
                              results["prosody_analysis"].get("Duration")),
                }
                segments.append(segment_data)

    if not segments:
        print(f"No valid segments found for audio: {audio_path}")
        return []

    # Analyze segments in context
    feedback = []
    low_pitch_streak = 0

    for i, segment in enumerate(segments):
        if segment["pitch_variance"] is None:
            continue

        # Check individual segment
        pitch_feedback = None
        if segment["pitch_variance"] < threshold:
            low_pitch_streak += 1
            severity = "high" if segment["pitch_variance"] < threshold / 2 else "medium"
            pitch_feedback = {
                "segment_index": i + 1,
                "text": segment["text"],
                "pitch_variance": segment["pitch_variance"],
                "severity": severity,
                "message": (
                    f"Low pitch variation detected ({segment['pitch_variance']:.1f} Hz). "
                    "Try to add more vocal variety."
                ),
            }
        else:
            low_pitch_streak = 0
            if segment["pitch_variance"] > threshold * 1.5:
                pitch_feedback = {
                    "segment_index": i + 1,
                    "text": segment["text"],
                    "pitch_variance": segment["pitch_variance"],
                    "severity": "medium",
                    "message": (
                        f"Very high pitch variation ({segment['pitch_variance']:.1f} Hz). "
                        "Consider moderating your pitch variation for more natural delivery."
                    ),
                }

        # Add feedback if needed
        if pitch_feedback:
            feedback.append(pitch_feedback)

        # Add streak feedback if applicable
        if low_pitch_streak == 3:
            feedback.append({
                "segment_index": i - 1,  # Point to the middle segment of the streak
                "severity": "high",
                "streak": True,
                "message": (
                    "Multiple consecutive segments with low pitch variation detected. "
                    "Try to incorporate more vocal dynamics in your speech."
                ),
            })

    # Generate summary feedback
    if feedback:
        avg_variance = np.mean(
            [s["pitch_variance"] for s in segments if s["pitch_variance"] is not None]
        )
        summary = {
            "type": "summary",
            "average_pitch_variance": avg_variance,
            "total_segments": len(segments),
            "segments_with_issues": len([f for f in feedback if not f.get("streak", False)]),
            "message": (
                f"Overall average pitch variance: {avg_variance:.1f} Hz. "
                f"Issues detected in {len([f for f in feedback if not f.get('streak', False)])} "
                f"out of {len(segments)} segments."
            ),
        }
        feedback.append(summary)

    return feedback

def print_pitch_feedback(feedback):
    """
    Print pitch analysis feedback in a formatted way.
    """
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

if __name__ == "__main__":
    sys.stdout = Logger("results/two_sentences_output.txt")
    data_folder = "data"
    sample_rate = 16000
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    cache = AudioAnalysisCache("cache/cache_data.json")

    # Process speech from the cloud
    file_url = "https://drive.google.com/uc?id=1ZjeYD6ceGylJtfTbP2BoGQg0nolzVUPv"
    process_speech_from_cloud(file_url, cache)

    # Analyze pitch variance and provide feedback
    print("\nAnalyzing pitch patterns across segments...")
    pitch_feedback = analyze_pitch_segments(cache, "data/audio_from_cloud.wav", threshold=20)
    print_pitch_feedback(pitch_feedback)
