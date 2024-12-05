import librosa
import numpy as np

def analyze_prosody(audio, sr):
    # Pitch analysis
    pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
    pitch_contour = pitches[pitches > 0]  # Exclude zeros
    pitch_variation = np.std(pitch_contour) if len(pitch_contour) > 0 else 0

    # Tempo analysis
    tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    duration = librosa.get_duration(y=audio, sr=sr)
    words_per_minute = (tempo / duration) * 60

    return {
        "Pitch Variation": pitch_variation,
        "Tempo (WPM)": words_per_minute
    }
