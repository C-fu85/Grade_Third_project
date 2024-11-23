import cntext
import jieba
import opencc

# 建立簡轉繁轉換器
converter = opencc.OpenCC('s2t')

def analyze_sentiment(text):
    # 將文本轉換為繁體
    text = converter.convert(text)
    
    # 使用 cntext 進行情感分析
    result = cntext.sentiment(text)
    
    # result 會返回一個字典，包含情感極性和信心分數
    # 例如：{'sentiment': 'positive', 'score': 0.9}
    return result

# 測試評論
測試評論 = [
    "這部電影真的很精彩，劇情緊湊，演員演技都很好。",
    "劇情很無聊，演員表演很差勁，浪費時間。",
    "特效做得不錯，但是故事情節太過牽強。",
    "整體來說是一部優秀的作品，值得推薦。",
    "這個產品品質很好，使用起來很方便。",
    "商品收到就壞了，客服態度也很差。"
]

print("\n測試結果：")
for i, 評論 in enumerate(測試評論, 1):
    結果 = analyze_sentiment(評論)
    print(f"\n評論{i}: {評論}")
    print(f"情感分析結果: {結果}")

# 儲存結果
with open('sentiment_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write('測試案例結果:\n')
    for i, 評論 in enumerate(測試評論, 1):
        結果 = analyze_sentiment(評論)
        f.write(f'\n評論{i}: {評論}\n')
        f.write(f'情感分析結果: {結果}\n')