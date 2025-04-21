import sys
import io
import time
from models.sentiment_analyzer import SentimentAnalyzer as NLTKAnalyzer
from models.paddle_analyzer import PaddleSentimentAnalyzer
from models.speech_processor import SpeechProcessor
from models.audio_analyzer import AudioAnalyzer

# 設置輸出編碼
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SpeechSentimentAnalysis:
    def __init__(self):
        self.nltk_analyzer = NLTKAnalyzer()
        self.paddle_analyzer = PaddleSentimentAnalyzer()
        self.speech_processor = SpeechProcessor()
        self.audio_analyzer = AudioAnalyzer()
    
    def analyze(self, audio_path):
        # 語音轉文字
        transcription = self.speech_processor.transcribe_audio(audio_path)
        
        # 分析每個片段
        segments_analysis = []
        total_words = 0
        total_duration = 0
        
        for segment in transcription['segments']:
            text = segment['text']
            
            # NLTK 分析
            nltk_start = time.time()
            nltk_sentiment = self.nltk_analyzer.analyze_sentiment(text)
            nltk_time = time.time() - nltk_start
            
            # Paddle 分析
            paddle_start = time.time()
            paddle_sentiment, paddle_score = self.paddle_analyzer.analyze_sentiment(text)
            paddle_time = time.time() - paddle_start
            
            segment_info = {
                'text': text,
                'start_time': segment['start'],
                'end_time': segment['end'],
                'nltk_sentiment': nltk_sentiment,
                'nltk_time': nltk_time,
                'paddle_sentiment': paddle_sentiment,
                'paddle_score': paddle_score,
                'paddle_time': paddle_time,
                'word_count': len(text)
            }
            segments_analysis.append(segment_info)
            
            total_words += len(text)
            total_duration += segment['end'] - segment['start']
        
        # 音頻特徵分析
        self.audio_analyzer.analyze_audio_features(audio_path)
        
        return {
            'segments': segments_analysis,
            'total_words': total_words,
            'total_duration': total_duration,
            'overall_wpm': (total_words / total_duration) * 60 if total_duration > 0 else 0
        }
    
    def save_results(self, results, filename='./results/speech_sentiment_analysis_results.txt'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("語音情感分析結果\n\n")
            f.write(f"總字數: {results['total_words']}\n")
            f.write(f"總時長: {results['total_duration']:.2f}秒\n")
            f.write(f"平均語速: {results['overall_wpm']:.2f} 字/分鐘\n\n")
            
            f.write("分段分析：\n")
            for segment in results['segments']:
                f.write(f"\n時間段: {segment['start_time']:.2f}s - {segment['end_time']:.2f}s\n")
                f.write(f"文本: {segment['text']}\n")
                f.write(f"NLTK情感分析: {segment['nltk_sentiment']} "
                       f"(耗時: {segment['nltk_time']*1000:.2f}ms)\n")
                f.write(f"Paddle情感分析: {segment['paddle_sentiment']} "
                       f"(置信度: {segment['paddle_score']:.2f}, "
                       f"耗時: {segment['paddle_time']*1000:.2f}ms)\n")
                f.write(f"字數: {segment['word_count']}\n")
                f.write(f"模型一致性: {'一致' if segment['nltk_sentiment'] == segment['paddle_sentiment'] else '不一致'}\n")

if __name__ == "__main__":
    analyzer = SpeechSentimentAnalysis()
    audio_path = "./data/路過人間 郁可唯.mp3"
    results = analyzer.analyze(audio_path)
    analyzer.save_results(results)
    print("\n分析結果已保存到 speech_sentiment_analysis_results.txt") 