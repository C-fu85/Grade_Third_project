import whisper
import jieba
import opencc
from nltk.classify import NaiveBayesClassifier
import nltk
import random
import numpy as np

# 訓練情感分析模型的模組（直接引用你的情感分析代碼）
def prepare_sentiment_analysis_model():
    from datasets import load_dataset
    from tqdm import tqdm
    import gc  # 垃圾回收

    converter = opencc.OpenCC('s2t')
    dataset1 = load_dataset("t1annnnn/Chinese_sentimentAnalyze")
    dataset2 = load_dataset("kenhktsui/chinese_sentiment_syn")

    max_samples = 50000
    train_data1 = dataset1['train']
    if len(train_data1) > max_samples:
        indices = random.sample(range(len(train_data1)), max_samples)
        train_data1 = train_data1.select(indices)

    train_size1 = int(len(train_data1) * 0.8)
    train_data1 = train_data1.select(range(train_size1))

    train_data2 = dataset2['train']
    if len(train_data2) > max_samples:
        indices = random.sample(range(len(train_data2)), max_samples)
        train_data2 = train_data2.select(indices)

    train_size2 = int(len(train_data2) * 0.8)
    train_data2 = train_data2.select(range(train_size2))

    def prepare_documents(data):
        documents = []
        for item in data:
            review = converter.convert(item['text'])
            words = list(jieba.cut(review))
            sentiment = 1 if item['label'] == 1 else 0
            documents.append((words, sentiment))
        return documents

    train_documents = prepare_documents(train_data1) + prepare_documents(train_data2)
    random.shuffle(train_documents)

    all_words = []
    for words, _ in train_documents:
        all_words.extend(words)

    word_freq = nltk.FreqDist(all_words)
    word_features = list(word_freq.keys())[:1000]
    del all_words
    gc.collect()

    def document_features(document):
        document_words = set(document)
        features = {}
        for word in word_features:
            features[f'包含({word})'] = (word in document_words)
        return features

    train_featuresets = [(document_features(d), c) for (d, c) in train_documents]
    del train_documents
    gc.collect()

    classifier = NaiveBayesClassifier.train(train_featuresets)
    return classifier, word_features

# 初始化情感分析模型
print("準備情感分析模型...")
sentiment_classifier, word_features = prepare_sentiment_analysis_model()
print("情感分析模型已準備完成！")

def document_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features[f'包含({word})'] = (word in document_words)
    return features

def 情感分析(文本):
    文本 = opencc.OpenCC('s2t').convert(文本)
    words = list(jieba.cut(文本))
    features = document_features(words)
    預測結果 = sentiment_classifier.classify(features)
    return "正面" if 預測結果 == 1 else "負面"

# Whisper 模型
print("載入 Whisper 模型...")
model = whisper.load_model("small")

# 轉錄語音
audio_path = r"路過人間 郁可唯.mp3"
print(f"處理音檔：{audio_path}")
result = model.transcribe(audio_path)

# 處理每句話的情感分析
print("\n分析轉錄結果的情感...")
sentiments = []
for i, segment in enumerate(result['segments']):
    text = segment['text']
    sentiment = 情感分析(text)
    sentiments.append((text, sentiment))
    print(f"句子 {i+1}: {text}")
    print(f"情感分析結果: {sentiment}\n")

# 保存分析結果
output_path = "speech_sentiment_analysis_results.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("轉錄結果及情感分析：\n")
    for i, (text, sentiment) in enumerate(sentiments, 1):
        f.write(f"句子 {i}: {text}\n")
        f.write(f"情感分析結果: {sentiment}\n\n")

print(f"結果已保存到 {output_path}")