import gdown
from moviepy.editor import VideoFileClip
import whisper
from pydub import AudioSegment

def download_file_from_cloud(url, output_path):
    """
    下載檔案（例如從Google Drive或AWS S3）
    """
    gdown.download(url, output_path, quiet=False)

def convert_m4a_to_wav(m4a_path, wav_path):
    """
    將 M4A 檔案轉換為 WAV 格式
    """
    try:
        audio = AudioSegment.from_file(m4a_path, format="m4a")
        audio.export(wav_path, format="wav")
        print(f"Converted {m4a_path} to {wav_path}")
    except Exception as e:
        print(f"Error converting file: {e}")

def extract_audio_from_video(video_path, output_audio_path):
    """
    從影片中提取音訊
    """
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(output_audio_path, codec='pcm_s16le')

def transcribe_audio_to_sentences(audio_path):
    """
    使用Whisper將音訊轉為文本並切割為句子
    """
    model = whisper.load_model("small")
    result = model.transcribe(audio_path)
    sentences = result['text'].split('.')  # 使用句號切割句子
    return sentences, result['segments']
