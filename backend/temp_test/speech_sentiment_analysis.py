import whisper
import librosa
import numpy as np
import matplotlib.pyplot as plt
import sys
import io
import jieba
import nltk
from nltk.classify import NaiveBayesClassifier
import random
import opencc
from datasets import load_dataset
from tqdm import tqdm
import gc

# 設置輸出編碼
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SpeechSentimentAnalyzer:
    def __init__(self):
        print("初始化模型中...")
        # 首先初始化 converter
        self.converter = opencc.OpenCC('s2t')
        
        # 初始化 Whisper
        self.whisper_model = whisper.load_model("small")
        
        # 最後初始化情感分析模型
        self.init_sentiment_model()
        
    def init_sentiment_model(self):
        print('載入情感分析數據集...')
        # 載入數據集
        dataset1 = load_dataset("t1annnnn/Chinese_sentimentAnalyze")
        dataset2 = load_dataset("kenhktsui/chinese_sentiment_syn")
        
        # 設定採樣數量
        max_samples = 50000

        # 從第一個數據集取樣並分割
        train_data1 = dataset1['train']
        if len(train_data1) > max_samples:
            indices = random.sample(range(len(train_data1)), max_samples)
            train_data1 = train_data1.select(indices)

        # 分割第一個數據集的訓練集
        train_size1 = int(len(train_data1) * 0.8)
        train_indices1 = range(train_size1)
        test_indices1 = range(train_size1, len(train_data1))
        test_data1 = train_data1.select(test_indices1)
        train_data1 = train_data1.select(train_indices1)

        # 從第二個數據集取樣並分割
        train_data2 = dataset2['train']
        if len(train_data2) > max_samples:
            indices = random.sample(range(len(train_data2)), max_samples)
            train_data2 = train_data2.select(indices)

        # 分割第二個數據集的訓練集
        train_size2 = int(len(train_data2) * 0.8)
        train_indices2 = range(train_size2)
        test_indices2 = range(train_size2, len(train_data2))
        test_data2 = train_data2.select(test_indices2)
        train_data2 = train_data2.select(train_indices2)

        print(f'數據集1 - 訓練集大小: {len(train_data1)}, 測試集大小: {len(test_data1)}')
        print(f'數據集2 - 訓練集大小: {len(train_data2)}, 測試集大小: {len(test_data2)}')

        def prepare_documents(data, desc):
            documents = []
            for item in tqdm(data, desc=desc):
                review = self.converter.convert(item['text'])
                words = list(jieba.cut(review))
                sentiment = 1 if item['label'] == 1 else 0
                documents.append((words, sentiment))
            return documents

        print('處理第一個數據集的訓練數據...')
        train_documents1 = prepare_documents(train_data1, "處理數據集1訓練數據")
        print('處理第一個數據集的測試數據...')
        test_documents1 = prepare_documents(test_data1, "處理數據集1測試數據")

        print('處理第二個數據集的訓練數據...')
        train_documents2 = prepare_documents(train_data2, "處理數據集2訓練數據")
        print('處理第二個數據集的測試數據...')
        test_documents2 = prepare_documents(test_data2, "處理數據集2測試數據")

        # 合併兩個數據集的文檔
        train_documents = train_documents1 + train_documents2
        test_documents = test_documents1 + test_documents2

        # 打亂合併後的數據
        random.shuffle(train_documents)
        random.shuffle(test_documents)

        print('建立特徵集...')
        all_words = []
        for words, _ in tqdm(train_documents, desc="統計詞頻"):
            all_words.extend(words)

        word_freq = nltk.FreqDist(all_words)
        self.word_features = list(word_freq.keys())[:1000]  # 使用1000個特徵
        del all_words
        gc.collect()

        def document_features(document):
            document_words = set(document)
            features = {}
            for word in self.word_features:
                features[f'包含({word})'] = (word in document_words)
            return features

        print('準備訓練特徵集...')
        train_featuresets = [(document_features(d), c) for (d, c) in tqdm(train_documents, desc="準備訓練特徵")]
        del train_documents
        gc.collect()

        print('準備測試特徵集...')
        test_featuresets = [(document_features(d), c) for (d, c) in tqdm(test_documents, desc="準備測試特徵")]
        del test_documents
        gc.collect()

        print('開始訓練分類器...')
        self.classifier = NaiveBayesClassifier.train(train_featuresets)

        accuracy = nltk.classify.accuracy(self.classifier, test_featuresets)
        print(f'準確率: {accuracy:.4f}')
    
    def transcribe_audio(self, audio_path):
        """轉錄音頻並分析"""
        print("\n開始音頻轉錄...")
        result = self.whisper_model.transcribe(audio_path)
        
        segments_analysis = []
        total_words = 0
        total_duration = 0
        
        print("\n分段分析結果：")
        for segment in result['segments']:
            text = segment['text']
            start_time = segment['start']
            end_time = segment['end']
            segment_duration = end_time - start_time
            
            # 情感分析
            sentiment = self.analyze_sentiment(text)
            
            # 統計信息
            word_count = len(text)
            total_words += word_count
            total_duration += segment_duration
            
            segment_info = {
                'text': text,
                'start_time': start_time,
                'end_time': end_time,
                'sentiment': sentiment,
                'word_count': word_count
            }
            segments_analysis.append(segment_info)
            
            # 打印分段結果
            print(f"\n時間段: {start_time:.2f}s - {end_time:.2f}s")
            print(f"文本: {text}")
            print(f"情感: {sentiment}")
            
        # 計算整體統計
        overall_wpm = (total_words / total_duration) * 60 if total_duration > 0 else 0
        
        # 分析音頻特徵
        self.analyze_audio_features(audio_path)
        
        return {
            'segments': segments_analysis,
            'total_words': total_words,
            'total_duration': total_duration,
            'overall_wpm': overall_wpm
        }
    
    def analyze_sentiment(self, text):
        """情感分析"""
        text = self.converter.convert(text)
        words = list(jieba.cut(text))
        features = self.document_features(words)
        prediction = self.classifier.classify(features)
        return "正面" if prediction == 1 else "負面"
    
    def document_features(self, document):
        """提取文本特徵"""
        document_words = set(document)
        features = {}
        for word in self.word_features:
            features[f'包含({word})'] = (word in document_words)
        return features
    
    def analyze_audio_features(self, audio_path):
        """分析音頻特徵"""
        print("\n分析音頻特徵...")
        y, sr = librosa.load(audio_path, sr=None)
        
        # 計算音頻能量
        frame_length = 1024
        hop_length = 512
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
        
        # 檢測停頓
        threshold = 0.02
        silent_frames = np.where(energy < threshold)[1]
        
        # 繪製圖表
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

# 使用示例
if __name__ == "__main__":
    analyzer = SpeechSentimentAnalyzer()
    
    # 分析音頻文件
    audio_path = "..\大三專題\路過人間 郁可唯.mp3"
    results = analyzer.transcribe_audio(audio_path)
    
    # 保存結果
    with open('speech_sentiment_analysis_results.txt', 'w', encoding='utf-8') as f:
        f.write("語音情感分析結果\n\n")
        f.write(f"總字數: {results['total_words']}\n")
        f.write(f"總時長: {results['total_duration']:.2f}秒\n")
        f.write(f"平均語速: {results['overall_wpm']:.2f} 字/分鐘\n\n")
        
        f.write("分段分析：\n")
        for segment in results['segments']:
            f.write(f"\n時間段: {segment['start_time']:.2f}s - {segment['end_time']:.2f}s\n")
            f.write(f"文本: {segment['text']}\n")
            f.write(f"情感: {segment['sentiment']}\n")
            f.write(f"字數: {segment['word_count']}\n")
            
    print("\n分析結果已保存到 speech_sentiment_analysis_results.txt") 