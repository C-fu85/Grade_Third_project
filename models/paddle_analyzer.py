from paddlenlp import Taskflow
import paddle
import opencc

class PaddleSentimentAnalyzer:
    def __init__(self):
        print("初始化 Paddle 情感分析模型...")
        self.converter = opencc.OpenCC('s2t')
        # 初始化 PaddleNLP 情感分析模型
        self.model = Taskflow("sentiment_analysis", 
                            model="skep_ernie_1.0_large_ch",
                            device_id=0 if paddle.device.is_compiled_with_cuda() else -1)
    
    def analyze_sentiment(self, text):
        """
        分析文本情感
        返回: "正面" 或 "負面"，以及置信度
        """
        try:
            # 將繁體轉換為簡體
            text = self.converter.convert(text)
            
            # 進行情感分析
            result = self.model(text)
            
            # 獲取結果
            if result and len(result) > 0:
                label = result[0]['label']
                score = result[0]['score']
                sentiment = "正面" if label == "positive" else "負面"
                return sentiment, score
            
            return "無法判斷", 0.0
            
        except Exception as e:
            print(f"Paddle情感分析過程中發生錯誤: {str(e)}")
            return "分析錯誤", 0.0 