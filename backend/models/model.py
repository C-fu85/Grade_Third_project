from transformers import pipeline

# Load the model locally

MODEL_PATH = r"E:\code\Grade_Third_project\stutter_detection_model"  # 使用原始字符串避免反斜杠問題
pipe = pipeline("audio-classification", model=MODEL_PATH, device=0)
# Load your audio file
audio_file = "backend/data/male01.wav"  # Replace with your audio file path

# Use the pipeline for inference
result = pipe(audio_file)

# Output the result
print(result)

