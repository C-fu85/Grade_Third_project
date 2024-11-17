import tensorflow as tf
import librosa
import numpy as np
from vggish_input import waveform_to_examples
from vggish_postprocess import Postprocessor

# 加載預訓練模型
vggish_checkpoint = "models/research/audioset/vggish_model.ckpt"
vggish_saver = tf.train.Saver()
with tf.Session() as sess:
    vggish_saver.restore(sess, vggish_checkpoint)

    # 音頻文件路徑
    audio_path = r"C:\Users\fu\Downloads\路過人間 郁可唯.mp3"
    y, sr = librosa.load(audio_path, sr=16000)

    # 將音頻轉換為VGGish模型輸入格式
    examples = waveform_to_examples(y)

    # 提取VGGish特徵
    [embedding] = sess.run([embedding_tensor], feed_dict={waveform_input_tensor: examples})

    # 可以進行後處理（例如標準化、降維等）
    pproc = Postprocessor("vggish_pca_params.npz")
    processed_embedding = pproc.postprocess(embedding)

    print("VGGish Feature Embedding: ", processed_embedding)
