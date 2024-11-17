import nltk
nltk.download('punkt')  # Download basic tokenizer data
nltk.download('movie_reviews') 
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


from nltk.classify import NaiveBayesClassifier

# 訓練分類器
classifier = NaiveBayesClassifier.train(train_set)

# 查看模型在測試集上的準確率
print('Accuracy:', nltk.classify.accuracy(classifier, test_set))


def sentiment_analysis(text):
    tokens = nltk.word_tokenize(text)
    features = document_features(tokens)
    return classifier.classify(features)

# 測試情感分析模型
review1 = "This movie is great and fantastic!"
review2 = "I disliked this film. It was boring."

print("Review 1:", sentiment_analysis(review1))
print("Review 2:", sentiment_analysis(review2))
