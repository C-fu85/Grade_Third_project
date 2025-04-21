import whisper
import os

def transcribe_audio(audio_path, model_size="small"):
    """
    將語音檔案轉換為文字
    
    參數:
        audio_path: 音頻文件路徑
        model_size: 模型大小 ("tiny", "base", "small", "medium", "large")
    """
    try:
        # 檢查文件是否存在
        if not os.path.exists(audio_path):
            print(f"錯誤：找不到音頻文件：{audio_path}")
            return None
            
        print(f"載入 {model_size} 模型中...")
        model = whisper.load_model(model_size)
        
        print("開始轉錄...")
        result = model.transcribe(audio_path)
        
        return result["text"]
        
    except Exception as e:
        print(f"轉錄過程中發生錯誤: {str(e)}")
        return None

if __name__ == "__main__":
    # 音頻文件路徑
    audio_path = r"C:\Users\fu\Downloads\新錄音-2024-11-23-下午-04-37-00.aac"
    
    # 轉錄音頻
    text = transcribe_audio(audio_path)
    
    if text:
        print("\n轉錄結果：")
        print(text)
        
        # 保存結果到文件
        with open("./results/test_transcription_result.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("\n結果已保存到 transcription_result.txt")