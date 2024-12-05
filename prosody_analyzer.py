import librosa
import numpy as np

def analyze_prosody(audio_path, sample_rate=16000):
    """
    分析音檔的韻律
    
    參數:
    - audio_path: 資料路徑
    - sample_rate: (default 16kHz)

    Example return: 
    Pitch Mean: 218.04
    Pitch Variation: 26.56
    Energy Mean: 0.07
    Energy Variation: 0.06
    """
    try:
        audio, sr = librosa.load(audio_path, sr=sample_rate)
        
        # 一般化[-1, 1] range
        audio = audio / np.max(np.abs(audio))
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        return None

    # Pitch detection
    pitch_values, voiced_flag, voiced_probs = librosa.pyin(audio, fmin=librosa.note_to_hz('C1'), fmax=librosa.note_to_hz('C7'))
    pitch_values = pitch_values[voiced_flag]

    # 把pitch values轉成可用的數值 80Hz -> 600Hz
    pitch_values = [p for p in pitch_values if 80 < p < 600]
    
    pitch_mean = np.mean(pitch_values) if pitch_values else 0
    pitch_variation = np.std(pitch_values) if pitch_values else 0

    # Energy (音量)
    rms_energy = librosa.feature.rms(y=audio).flatten()
    energy_mean = np.mean(rms_energy)
    energy_variation = np.std(rms_energy)

    return {
        "Pitch Mean": pitch_mean,
        "Pitch Variation": pitch_variation,
        "Energy Mean": energy_mean,
        "Energy Variation": energy_variation,
    }

