import moviepy.editor as mp

# Try loading a video file to test if ffmpeg is accessible
video = mp.VideoFileClip("data/test.wav")
print(video.reader.fps)