import jieba
import nltk
from nltk.classify import NaiveBayesClassifier
import random
from datasets import load_dataset
from tqdm import tqdm
import gc
import opencc

class SentimentAnalyzer:
    def __init__(self):
        self.converter = opencc.OpenCC('s2t')
        self.word_features = []
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

        print('準備訓練特徵集...')
        train_featuresets = [(self.document_features(d), c) for (d, c) in tqdm(train_documents, desc="準備訓練特徵")]
        del train_documents
        gc.collect()

        print('準備測試特徵集...')
        test_featuresets = [(self.document_features(d), c) for (d, c) in tqdm(test_documents, desc="準備測試特徵")]
        del test_documents
        gc.collect()

        print('開始訓練分類器...')
        self.classifier = NaiveBayesClassifier.train(train_featuresets)

        accuracy = nltk.classify.accuracy(self.classifier, test_featuresets)
        print(f'準確率: {accuracy:.4f}')
    
    def analyze_sentiment(self, text):
        text = self.converter.convert(text)
        words = list(jieba.cut(text))
        features = self.document_features(words)
        prediction = self.classifier.classify(features)
        return "正面" if prediction == 1 else "負面"
    
    def document_features(self, document):
        document_words = set(document)
        features = {}
        for word in self.word_features:
            features[f'包含({word})'] = (word in document_words)
        return features