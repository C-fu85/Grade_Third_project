import librosa
import numpy as np

def analyze_prosody(audio_path, start_time=None, end_time=None, sample_rate=16000):
    """
    Optimized function to analyze prosody features of an audio segment.
    """
    try:
        # Load a segment of the audio if start_time and end_time are specified
        duration = end_time - start_time if start_time is not None and end_time is not None else None
        audio, sr = librosa.load(audio_path, sr=sample_rate, offset=start_time or 0, duration=duration)

        if audio is None or len(audio) == 0:
            print(f"Error: Audio file {audio_path} could not be loaded or is empty.")
            return None

        # Normalize audio to [-1, 1]
        audio = librosa.util.normalize(audio)
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        return None

    try:
        # Efficiently compute pitch with adaptive fmin and fmax
        pitch_values, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),  # Reduced range for common speech
            fmax=librosa.note_to_hz('C6')
        )

        # Filter valid pitch values
        pitch_values = pitch_values[voiced_flag]
        pitch_values = pitch_values[(pitch_values > 80) & (pitch_values < 600)]

        # Compute pitch statistics
        pitch_mean = np.mean(pitch_values) if len(pitch_values) > 0 else 0
        pitch_variation = np.std(pitch_values) if len(pitch_values) > 0 else 0

        # Efficiently compute RMS energy
        rms_energy = librosa.feature.rms(y=audio).flatten()
        energy_mean = np.mean(rms_energy)
        energy_variation = np.std(rms_energy)

        return {
            "Pitch Mean": pitch_mean,
            "Pitch Variation": pitch_variation,
            "Energy Mean": energy_mean,
            "Energy Variation": energy_variation,
        }
    except Exception as e:
        print(f"Error during feature extraction: {e}")
        return None


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