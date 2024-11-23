import librosa
import numpy as np
import matplotlib.pyplot as plt

class AudioAnalyzer:
    def analyze_audio_features(self, audio_path):
        print("\n分析音頻特徵...")
        y, sr = librosa.load(audio_path, sr=None)
        
        # 計算音頻能量
        frame_length = 1024
        hop_length = 512
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
        
        # 檢測停頓
        threshold = 0.02
        silent_frames = np.where(energy < threshold)[1]
        
        self._plot_audio_features(y, energy, silent_frames, hop_length, threshold)
        
        return {
            'energy': energy,
            'silent_frames': silent_frames,
            'sample_rate': sr
        }
    
    def _plot_audio_features(self, y, energy, silent_frames, hop_length, threshold):
        plt.figure(figsize=(12, 6))
        
        # 能量圖
        plt.subplot(2, 1, 1)
        plt.plot(energy[0], label='Energy')
        plt.axhline(y=threshold, color='r', linestyle='--', label='Energy Threshold')
        plt.legend()
        plt.title("Energy vs. Threshold")
        plt.xlabel("Frames")
        plt.ylabel("Energy")
        
        # 波形圖
        plt.subplot(2, 1, 2)
        plt.plot(y)
        plt.scatter(silent_frames * hop_length, y[silent_frames * hop_length], 
                   color='red', label="Pause")
        plt.legend()
        plt.title("Audio Signal with Pauses")
        plt.xlabel("Samples")
        plt.ylabel("Amplitude")
        
        plt.tight_layout()
        plt.show() 