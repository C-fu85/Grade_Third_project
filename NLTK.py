import nltk

from nltk.corpus import movie_reviews

nltk.download('movie_reviews')

# 準備訓練資料集
documents = [(list(movie_reviews.words(fileid)), category)
             for category in movie_reviews.categories()
             for fileid in movie_reviews.fileids(category)]

# 打亂資料順序以增加模型的泛化能力
import random
random.shuffle(documents)

# 準備特徵集
all_words = nltk.FreqDist(w.lower() for w in movie_reviews.words())
word_features = list(all_words.keys())[:2000]  # 選取最常見的2000個單詞作為特徵

def document_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains({})'.format(word)] = (word in document_words)
    return features

featuresets = [(document_features(d), c) for (d,c) in documents]
train_set, test_set = featuresets[100:], featuresets[:100]  # 分割訓練集和測試集
