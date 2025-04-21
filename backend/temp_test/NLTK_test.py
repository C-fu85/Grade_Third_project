import jieba
import nltk
from nltk.classify import NaiveBayesClassifier
import random
import opencc
from datasets import load_dataset
from tqdm import tqdm
import gc  # 垃圾回收

# 建立簡轉繁轉換器
converter = opencc.OpenCC('s2t')

print('載入數據集中...')
# 載入兩個數據集
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
        review = converter.convert(item['text'])
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
word_features = list(word_freq.keys())[:1000]  # 使用1000個特徵
del all_words
gc.collect()

def document_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
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
classifier = NaiveBayesClassifier.train(train_featuresets)

accuracy = nltk.classify.accuracy(classifier, test_featuresets)
print(f'準確率: {accuracy:.4f}')

def 情感分析(文本):
    文本 = converter.convert(文本)
    words = list(jieba.cut(文本))
    features = document_features(words)
    預測結果 = classifier.classify(features)
    return "正面" if 預測結果 == 1 else "負面"

# 測試評論
測試評論 = [
    # 電影相關評論
    "這部電影真的很精彩，劇情緊湊，演員演技都很好。",
    "劇情很無聊，演員表演很差勁，浪費時間。",
    "特效做得不錯，但是故事情節太過牽強。",
    "整體來說是一部優秀的作品，值得推薦。",
    
    # 產品相關評論
    "這個產品品質很好，使用起來很方便。",
    "商品收到就壞了，客服態度也很差。",
    "價格實惠，性能也不錯，推薦購買。",
    
    # 餐廳相關評論
    "這家餐廳的菜色很美味，服務態度也很好。",
    "等了一個小時才上菜，食物還是冷的。",
    "環境衛生，價格合理，會再來光顧。",
    
    # 複雜情感評論
    "畫面很漂亮，但劇情實在太差。",
    "服務態度不錯，可惜商品品質不佳。",
    "價格便宜，但品質也跟著差。",
    "雖然貴了點，但品質確實很好。"
]

print("\n測試結果：")
for i, 評論 in enumerate(測試評論, 1):
    結果 = 情感分析(評論)
    print(f"\n評論{i}: {評論}")
    print(f"情感分析結果: {結果}")

# 計算統計結果
正面評論數 = sum(1 for 評論 in 測試評論 if 情感分析(評論) == "正面")
負面評論數 = len(測試評論) - 正面評論數

print("\n統計結果：")
print(f"總評論數: {len(測試評論)}")
print(f"正面評論數: {正面評論數}")
print(f"負面評論數: {負面評論數}")
print(f"正面評論比例: {(正面評論數/len(測試評論))*100:.2f}%")

# 儲存結果
with open('sentiment_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write(f'模型準確率: {accuracy:.4f}\n')
    f.write(f'使用的特徵數量: {len(word_features)}\n')
    f.write(f'總訓練數據量: {len(train_featuresets)}\n')
    f.write(f'總測試數據量: {len(test_featuresets)}\n\n')
    
    f.write('測試案例結果:\n')
    for i, 評論 in enumerate(測試評論, 1):
        結果 = 情感分析(評論)
        f.write(f'\n評論{i}: {評論}\n')
        f.write(f'情感分析結果: {結果}\n')
    
    f.write('\n\n統計結果：\n')
    f.write(f"總評論數: {len(測試評論)}\n")
    f.write(f"正面評論數: {正面評論數}\n")
    f.write(f"負面評論數: {負面評論數}\n")
    f.write(f"正面評論比例: {(正面評論數/len(測試評論))*100:.2f}%\n")

print("\n結果已保存到 sentiment_analysis_results.txt")
