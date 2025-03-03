# train_audio_emotion_model.py
import os
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import HubertForCTC, Wav2Vec2Processor # type: ignore
import librosa

class AudioEmotionDataset(Dataset):
    def __init__(self, root_dir):
        self.audio_files = []
        self.labels = []
        self.emotion_map = {
            "happy": 0,
            "sad": 1,
            "angry": 2,
            "surprised": 3,
            "fearful": 4,
            "neutral": 5
        }

        # 遍歷每個人的資料夾
        for person in os.listdir(root_dir):
            person_path = os.path.join(root_dir, person)
            if os.path.isdir(person_path):
                for emotion in self.emotion_map.keys():
                    emotion_path = os.path.join(person_path, emotion)
                    if os.path.isdir(emotion_path):
                        for audio_file in os.listdir(emotion_path):
                            if audio_file.endswith(".wav"):
                                self.audio_files.append(os.path.join(emotion_path, audio_file))
                                self.labels.append(self.emotion_map[emotion])

    def __len__(self):
        return len(self.audio_files)

    def __getitem__(self, idx):
        audio_path = self.audio_files[idx]
        y, sr = librosa.load(audio_path, sr=16000)
        label = self.labels[idx]
        return y, label

def train_model(audio_dir, epochs=5, batch_size=16):
    print("\n開始訓練模型...")

    # 加載 HuBERT 模型和處理器
    processor = Wav2Vec2Processor.from_pretrained("facebook/hubert-large-ls960")
    model = HubertForCTC.from_pretrained("facebook/hubert-large-ls960")
    model.train()

    # 初始化數據集和數據加載器
    dataset = AudioEmotionDataset(audio_dir)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

    for epoch in range(epochs):
        for batch in dataloader:
            inputs, labels = batch
            input_values = processor(inputs, sampling_rate=16000, return_tensors="pt", padding=True).input_values

            # 清除梯度
            optimizer.zero_grad()

            # 計算損失
            outputs = model(input_values, labels=labels)
            loss = outputs.loss

            # 反向傳播和優化
            loss.backward()
            optimizer.step()

            print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item()}")

    # 保存模型
    model.save_pretrained("trained_hubert_model")
    processor.save_pretrained("trained_hubert_model")

if __name__ == "__main__":
    # 音頻資料夾路徑
    audio_directory = "C:\\Users\\fu\\Downloads\\115f2-main\\115f2-main\\CASIA database\\CASIA database"
    train_model(audio_directory)