import whisper

class SpeechProcessor:
    def __init__(self):
        self.model = whisper.load_model("small").to("cuda")
    
    def transcribe_audio(self, audio_path):
        print("\n開始音頻轉錄...")
        result = self.model.transcribe(audio_path)
        return result 