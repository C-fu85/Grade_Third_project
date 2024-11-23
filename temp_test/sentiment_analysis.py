from paddlenlp import Taskflow
import opencc

class SentimentAnalyzer:
    def __init__(self):
        self.senta = Taskflow("sentiment_analysis")
        self.converter = opencc.OpenCC('t2s')  # 繁體轉簡體
        
    def analyze(self, text):
        # 轉換為簡體
        text = self.converter.convert(text)
        # 進行情感分析
        result = self.senta(text)
        return self._format_result(result[0])
    
    def _format_result(self, result):
        # 格式化結果
        return {
            "sentiment": "正面" if result['label'] == 'positive' else "負面",
            "score": result['score']
        }

# 使用示例
analyzer = SentimentAnalyzer()

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
    結果 = analyzer.analyze(評論)
    print(f"\n評論{i}: {評論}")
    print(f"情感分析結果: {結果}")

# 儲存結果
with open('sentiment_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write('測試案例結果:\n')
    for i, 評論 in enumerate(測試評論, 1):
        結果 = analyzer.analyze(評論)
        f.write(f'\n評論{i}: {評論}\n')
        f.write(f'情感分析結果: {結果}\n') 