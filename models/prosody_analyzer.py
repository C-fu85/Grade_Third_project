import librosa
import numpy as np

def analyze_prosody(audio_path, start_time=None, end_time=None, sample_rate=16000):
    """
    Analyzes prosody features of an audio segment.
    
    Args:
    - audio_path: File path to the audio.
    - start_time: Start time (in seconds) for the audio segment.
    - end_time: End time (in seconds) for the audio segment.
    - sample_rate: Sample rate (default is 16000).
    
    Returns:
    - Dictionary containing prosody features (pitch, energy, etc.).
    """
    try:
        # If start_time or end_time is None, load the entire audio file
        if start_time is None or end_time is None:
            audio, sr = librosa.load(audio_path, sr=sample_rate)
        else:
            duration = end_time - start_time
            audio, sr = librosa.load(audio_path, sr=sample_rate, offset=start_time, duration=duration)

        if audio is None or len(audio) == 0:
            print(f"Error: Audio file {audio_path} could not be loaded or is empty.")
            return None

        # Normalize the audio to the range [-1, 1]
        audio = audio / np.max(np.abs(audio))
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        return None

    # Pitch detection
    pitch_values, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=librosa.note_to_hz('C1'), fmax=librosa.note_to_hz('C7'))
    pitch_values = pitch_values[voiced_flag]

    # Filter pitch values between 80Hz and 600Hz
    pitch_values = [p for p in pitch_values if 80 < p < 600]
    
    pitch_mean = np.mean(pitch_values) if pitch_values else 0
    pitch_variation = np.std(pitch_values) if pitch_values else 0

    # Energy (volume)
    rms_energy = librosa.feature.rms(y=audio).flatten()
    energy_mean = np.mean(rms_energy)
    energy_variation = np.std(rms_energy)

    return {
        "Pitch Mean": pitch_mean,
        "Pitch Variation": pitch_variation,
        "Energy Mean": energy_mean,
        "Energy Variation": energy_variation,
    }
