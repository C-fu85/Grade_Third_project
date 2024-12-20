import os
import numpy as np
from pydub import AudioSegment
from prosody_analyzer import analyze_prosody

import ffmpeg

def convert_audio_to_wav(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith(".m4a") or file_name.endswith(".opus"):
            audio_path = os.path.join(input_dir, file_name)
            wav_name = os.path.splitext(file_name)[0] + ".wav"
            wav_path = os.path.join(output_dir, wav_name)

            try:
                ffmpeg.input(audio_path).output(wav_path).run()
                print(f"Converted {audio_path} to {wav_path}")
            except Exception as e:
                print(f"Error converting {audio_path}: {e}")


def calculate_distance(features, baseline):
    """
    Calculates the Euclidean distance between the features of an audio file and a baseline.

    Args:
        features (dict): Features of the audio file (Pitch Mean, Pitch Variation, Energy Mean, Energy Variation).
        baseline (dict): Baseline features to compare against.

    Returns:
        float: Euclidean distance between the features and the baseline.
    """
    return np.sqrt(
        (features['Pitch Mean'] - baseline['Pitch Mean']) ** 2 +
        (features['Pitch Variation'] - baseline['Pitch Variation']) ** 2 +
        (features['Energy Mean'] - baseline['Energy Mean']) ** 2 +
        (features['Energy Variation'] - baseline['Energy Variation']) ** 2
    )

def classify_gender(audio_path, male_baseline, female_baseline):
    """
    Classifies the gender of the speaker in an audio file based on prosody features.

    Args:
        audio_path (str): Path to the audio file.
        male_baseline (dict): Baseline features for male speakers.
        female_baseline (dict): Baseline features for female speakers.

    Returns:
        str: Predicted gender ('Male' or 'Female').
    """
    print(f"Classifying: {audio_path}")
    features = analyze_prosody(audio_path)

    if features is None:
        print(f"Failed to analyze prosody for {audio_path}")
        return "Unknown"

    male_distance = calculate_distance(features, male_baseline)
    female_distance = calculate_distance(features, female_baseline)

    print(f"Male Distance: {male_distance}, Female Distance: {female_distance}")

    return "Male" if male_distance < female_distance else "Female"

# Directories for audio files
input_dir = r"E:/Downloads/Downloads/tep"
output_wav_dir = r"E:/Downloads/Downloads/tep_wav"
male_output_dir = r"E:/Downloads/Downloads/male_classified"
female_output_dir = r"E:/Downloads/Downloads/female_classified"

# Convert audio files to WAV
#convert_audio_to_wav(input_dir, output_wav_dir)

# Ensure classification directories exist
os.makedirs(male_output_dir, exist_ok=True)
os.makedirs(female_output_dir, exist_ok=True)

# List of WAV files to classify
audio_files_to_classify = [
    os.path.join(output_wav_dir, file) for file in os.listdir(output_wav_dir) if file.endswith(".wav")
]

# Male and female baseline features
# Ensure these are pre-calculated and available
male_baseline = {
    "Pitch Mean": 210.18956,
    "Pitch Variation": 64.4286,
    "Energy Mean": 0.052295145,
    "Energy Variation": 0.049456336,
}
female_baseline = {
    "Pitch Mean": 290.169745691335,
    "Pitch Variation": 63.9335,
    "Energy Mean": 0.08601738,
    "Energy Variation": 0.060635347,
}

# Classify and move each WAV file
for audio_path in audio_files_to_classify:
    gender = classify_gender(audio_path, male_baseline, female_baseline)

    if gender == "Male":
        destination = os.path.join(male_output_dir, os.path.basename(audio_path))
    elif gender == "Female":
        destination = os.path.join(female_output_dir, os.path.basename(audio_path))
    else:
        print(f"Skipping file with unknown classification: {audio_path}")
        continue

    os.rename(audio_path, destination)
    print(f"Moved {audio_path} to {destination}")