import { useState, useRef, useEffect } from "react";

export default function LectureGuidanceSystem() {
  // 狀態管理
  const [textSegments, setTextSegments] = useState([]); // 語音轉錄結果
  const [pitchFeedback, setPitchFeedback] = useState([]); // 音調回饋
  const [stutterFeedback, setStutterFeedback] = useState([]); // 結巴回饋
  const [fileName, setFileName] = useState(""); // 上傳檔案名稱
  const [isProcessing, setIsProcessing] = useState(false); // 處理狀態
  const [currentTime, setCurrentTime] = useState(0); // 當前播放時間
  const [style, setStyle] = useState("default"); // 語音風格（default 或 passionate）
  const [audioUrl, setAudioUrl] = useState(null); // 音訊 URL
  const [viewMode, setViewMode] = useState("Feedback"); // 視圖模式（Feedback 或 Transcriptions）
  const audioRef = useRef(null); // 音訊播放器引用
  const [progressBarOffset, setProgressBarOffset] = useState(0); // 進度條偏移
  const [progressBarWidth, setProgressBarWidth] = useState(0); // 進度條寬度
  const [isRecording, setIsRecording] = useState(false); // 錄音狀態
  const mediaRecorderRef = useRef(null); // 錄音器引用
  const audioChunksRef = useRef([]); // 錄音數據片段

  // 處理檔案上傳並發送至後端進行分析
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setIsProcessing(true);
    setTextSegments([]);
    setPitchFeedback([]);
    setStutterFeedback([]);
    setCurrentTime(0);
    setAudioUrl(null);

    const formData = new FormData();
    formData.append("file", file);

    const url = `/api/transcribe?style=${encodeURIComponent(style)}`;

    try {
      const transcribeResponse = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!transcribeResponse.ok) {
        const errorData = await transcribeResponse.json();
        throw new Error(errorData.error || "轉錄失敗");
      }

      const transcribeData = await transcribeResponse.json();

      if (transcribeData.transcriptions || transcribeData.pitch_feedback || transcribeData.stutter_feedback) {
        setTextSegments(transcribeData.transcriptions || []);
        setPitchFeedback(transcribeData.pitch_feedback || []);
        setStutterFeedback(transcribeData.stutter_feedback || []);
        setCurrentTime(0);
        setAudioUrl(URL.createObjectURL(file));
      } else {
        setTextSegments([{ text: "無轉錄內容可用", start_time: 0, end_time: 0 }]);
        setPitchFeedback([]);
        setStutterFeedback([]);
      }
    } catch (error) {
      console.error("處理檔案時發生錯誤:", error);
      setTextSegments([{ text: "處理檔案時發生錯誤: " + error.message, start_time: 0, end_time: 0 }]);
      setPitchFeedback([]);
      setStutterFeedback([]);
    } finally {
      setIsProcessing(false);
    }
  };

  // 開始錄音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = handleRecordingStop;
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setFileName("錄音中...");
    } catch (error) {
      console.error("開始錄音失敗:", error);
      alert("無法開始錄音，請確認麥克風權限");
    }
  };

  // 停止錄音並處理
  const handleRecordingStop = async () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
    const audioFile = new File([audioBlob], "recording.wav", { type: "audio/wav" });
    
    setIsRecording(false);
    setFileName(audioFile.name);
    setIsProcessing(true);
    
    // 清理錄音資源
    mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    
    const formData = new FormData();
    formData.append("file", audioFile);

    const url = `/api/transcribe?style=${encodeURIComponent(style)}`;

    try {
      const transcribeResponse = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!transcribeResponse.ok) {
        const errorData = await transcribeResponse.json();
        throw new Error(errorData.error || "轉錄失敗");
      }

      const transcribeData = await transcribeResponse.json();

      if (transcribeData.transcriptions || transcribeData.pitch_feedback || transcribeData.stutter_feedback) {
        setTextSegments(transcribeData.transcriptions || []);
        setPitchFeedback(transcribeData.pitch_feedback || []);
        setStutterFeedback(transcribeData.stutter_feedback || []);
        setCurrentTime(0);
        setAudioUrl(URL.createObjectURL(audioFile));
      }
    } catch (error) {
      console.error("處理錄音時發生錯誤:", error);
      setTextSegments([{ text: "處理錄音時發生錯誤: " + error.message, start_time: 0, end_time: 0 }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // 監聽音訊播放時間與進度條尺寸
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    audio.addEventListener("timeupdate", updateTime);

    const calculateProgressBarBounds = () => {
      const audioElement = audioRef.current;
      if (!audioElement) return;

      const audioRect = audioElement.getBoundingClientRect();
      const totalWidth = audioRect.width;
      const leftControlsWidth = 120;
      const rightControlsWidth = 100;
      const progressWidth = totalWidth - leftControlsWidth - rightControlsWidth;

      setProgressBarOffset(leftControlsWidth);
      setProgressBarWidth(progressWidth);
    };

    audio.addEventListener("loadedmetadata", calculateProgressBarBounds);
    window.addEventListener("resize", calculateProgressBarBounds);
    calculateProgressBarBounds();

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("loadedmetadata", calculateProgressBarBounds);
      window.removeEventListener("resize", calculateProgressBarBounds);
    };
  }, [audioUrl]);

  // 清理 audioUrl 避免記憶體洩漏
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  // 格式化時間（秒數轉為 mm:ss）
  const formatTime = (seconds) => {
    const numSeconds = Number(seconds) || 0;
    const minutes = Math.floor(numSeconds / 60);
    const secs = Math.floor(numSeconds % 60);
    return `${minutes}:${secs < 10 ? "0" + secs : secs}`;
  };

  // 計算音訊總時長（使用 textSegments 中最大的 end_time）
  const totalDuration = textSegments.length > 0
    ? Math.max(
        ...textSegments
          .filter((item) => item.end_time !== undefined && !isNaN(item.end_time))
          .map((item) => Number(item.end_time)),
        1
      )
    : 0;

  // 跳轉到指定時間並播放
  const handleTimeJump = (startTime) => {
    if (audioRef.current) {
      audioRef.current.currentTime = startTime;
      audioRef.current.play();
    }
  };

  // 計算進度條上的標記位置
  const getMarkerPosition = (time) => {
    if (totalDuration === 0 || progressBarWidth === 0) return "0%";
    const positionRatio = time / totalDuration;
    const positionPercent = positionRatio;
    return `${positionPercent * 100}%`;
  };

  // 檢查語段是否需要改進（是否有音調或結巴回饋）
  const needsImprovement = (segment) => {
    const segmentStart = Number(segment.start_time);
    const segmentEnd = Number(segment.end_time);

    const hasStutterFeedback = stutterFeedback.some((item) => {
      if (item.type === "summary") return false;
      const feedbackStart = Number(item.start_time);
      const feedbackEnd = Number(item.end_time);
      return segmentStart <= feedbackEnd && segmentEnd >= feedbackStart;
    });

    const hasPitchFeedback = pitchFeedback.some((item) => {
      if (item.type === "summary") return false;
      const feedbackStart = Number(item.start_time);
      const feedbackEnd = Number(item.end_time);
      return segmentStart <= feedbackEnd && segmentEnd >= feedbackStart;
    });

    return hasStutterFeedback || hasPitchFeedback;
  };

  // 合併並按時間順序排序音調與結巴回饋
  const getSortedFeedback = () => {
    const pitchItems = pitchFeedback
      .filter((item) => item.type !== "summary")
      .map((item) => ({ ...item, feedbackType: "pitch" }));
    const stutterItems = stutterFeedback
      .filter((item) => item.type !== "summary")
      .map((item) => ({ ...item, feedbackType: "stutter" }));

    const allFeedback = [...pitchItems, ...stutterItems];
    return allFeedback.sort((a, b) => {
      const timeDiff = Number(a.start_time) - Number(b.start_time);
      if (timeDiff !== 0) return timeDiff;
      return a.feedbackType === "pitch" ? -1 : 1; // 相同時間時，音調回饋優先
    });
  };

  return (
    <div
      style={{
        padding: "1.5rem",
        width: "100%",
        boxSizing: "border-box",
        background: "linear-gradient(to bottom, #e0f7fa, #ffffff)",
      }}
    >
      <div style={{ maxWidth: "84rem", margin: "0 auto" }}>
        <div style={{ display: "flex", gap: "0.9rem", marginBottom: "0.9rem" }}>
          {/* 上傳與分析區塊 */}
          <div
            style={{
              width: "33.333%",
              minHeight: "400px",
              backgroundColor: "#ffffff",
              padding: "1.5rem",
              borderRadius: "0.5rem",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
            }}
          >
            <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "1rem" }}>
              上傳與分析
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <label
                  htmlFor="style"
                  style={{ display: "block", color: "#4B5563", marginBottom: "0.25rem" }}
                >
                  語音風格：
                </label>
                <select
                  id="style"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #D1D5DB",
                    borderRadius: "0.375rem",
                  }}
                >
                  <option value="default">預設</option>
                  <option value="passionate">熱情</option>
                </select>
              </div>
              <label
                style={{
                  display: "block",
                  width: "100%",
                  padding: "0.5rem",
                  backgroundColor: "#3B82F6",
                  color: "#ffffff",
                  textAlign: "center",
                  borderRadius: "0.375rem",
                  cursor: isProcessing || isRecording ? "not-allowed" : "pointer",
                }}
                onMouseOver={(e) => {
                  if (!isProcessing && !isRecording) e.currentTarget.style.backgroundColor = "#2563EB";
                }}
                onMouseOut={(e) => {
                  if (!isProcessing && !isRecording) e.currentTarget.style.backgroundColor = "#3B82F6";
                }}
              >
                <span>{isProcessing ? "處理中..." : "上傳檔案"}</span>
                <input
                  type="file"
                  style={{ display: "none" }}
                  accept=".mp3,.mp4,.wav,.m4a"
                  onChange={handleFileUpload}
                  disabled={isProcessing || isRecording}
                />
              </label>
              <button
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  backgroundColor: isRecording ? "#EF4444" : "#10B981",
                  color: "#ffffff",
                  textAlign: "center",
                  borderRadius: "0.375rem",
                  cursor: isProcessing ? "not-allowed" : "pointer",
                  border: "none",
                }}
                onMouseOver={(e) => {
                  if (!isProcessing) {
                    e.currentTarget.style.backgroundColor = isRecording ? "#DC2626" : "#059669";
                  }
                }}
                onMouseOut={(e) => {
                  if (!isProcessing) {
                    e.currentTarget.style.backgroundColor = isRecording ? "#EF4444" : "#10B981";
                  }
                }}
                onClick={isRecording ? () => mediaRecorderRef.current.stop() : startRecording}
                disabled={isProcessing}
              >
                {isRecording ? "停止錄音" : "開始錄音"}
              </button>
              {fileName && (
                <p style={{ fontSize: "0.875rem", color: "#6B7280" }}>已選擇：{fileName}</p>
              )}
              {isProcessing && (
                <p style={{ fontSize: "0.875rem", color: "#6B7280" }}>正在處理您的檔案...</p>
              )}
            </div>
          </div>

          {/* 大綱與建議區塊 */}
          <div
            style={{
              width: "66.667%",
              maxHeight: "400px",
              backgroundColor: "#ffffff",
              padding: "0 1.5rem 1.5rem 1.5rem",
              borderRadius: "0.5rem",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              overflowY: "auto",
              position: "relative",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
                position: "sticky",
                top: "-1.5rem",
                backgroundColor: "#ffffff",
                zIndex: 10,
                padding: "1.5rem 0 0.5rem 0",
                borderBottom: "1px solid #E5E7EB",
              }}
            >
              <h2 style={{ fontSize: "1.25rem", fontWeight: "600" }}>大綱與建議</h2>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  style={{
                    padding: "0.25rem 0.75rem",
                    borderRadius: "0.375rem",
                    backgroundColor: viewMode === "Feedback" ? "#3B82F6" : "#E5E7EB",
                    color: viewMode === "Feedback" ? "#ffffff" : "#4B5563",
                  }}
                  onClick={() => setViewMode("Feedback")}
                >
                  建議
                </button>
                <button
                  style={{
                    padding: "0.25rem 0.75rem",
                    borderRadius: "0.375rem",
                    backgroundColor: viewMode === "Transcriptions" ? "#3B82F6" : "#E5E7EB",
                    color: viewMode === "Transcriptions" ? "#ffffff" : "#4B5563",
                  }}
                  onClick={() => setViewMode("Transcriptions")}
                >
                  字幕
                </button>
              </div>
            </div>

            {viewMode === "Feedback" ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {(pitchFeedback.length > 0 || stutterFeedback.length > 0) && (
                  <>
                    {getSortedFeedback().map((item, index) => (
                      <div
                        key={`${item.feedbackType}-${index}`}
                        style={{
                          padding: "0.5rem",
                          backgroundColor: "#F9FAFB",
                          borderRadius: "0.375rem",
                          cursor: "pointer",
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#F3F4F6")}
                        onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "#F9FAFB")}
                        onClick={() => handleTimeJump(item.start_time)}
                      >
                        <p style={{ fontWeight: "500" }}>
                          [{formatTime(item.start_time)} - {formatTime(item.end_time)}] {item.text}
                        </p>
                        <p
                          style={{
                            color:
                              item.feedbackType === "pitch"
                                ? item.severity === "high"
                                  ? "#EF4444"
                                  : "#F59E0B"
                                : "#3B82F6",
                          }}
                        >
                          {item.message}
                        </p>
                      </div>
                    ))}
                    {getSortedFeedback().length === 0 && (
                      <p style={{ color: "#6B7280" }}>無段落回饋可用</p>
                    )}
                  </>
                )}

                {(pitchFeedback.some((item) => item.type === "summary") ||
                  stutterFeedback.some((item) => item.type === "summary")) && (
                  <>
                    <h3 style={{ fontSize: "1.125rem", fontWeight: "500", marginTop: "1rem" }}>
                      總結
                    </h3>
                    {pitchFeedback.map((item, index) =>
                      item.type === "summary" ? (
                        <div
                          key={`pitch-summary-${index}`}
                          style={{
                            padding: "0.5rem",
                            backgroundColor: "#F9FAFB",
                            borderRadius: "0.375rem",
                          }}
                        >
                          <h4 style={{ fontWeight: "500", marginBottom: "0.5rem" }}>
                            音調總結
                          </h4>
                          <p>{item.message}</p>
                          {item.metrics && (
                            <div style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
                              <p>音調變化：{item.metrics.average_pitch_variance.toFixed(1)} Hz</p>
                              <p>語速：{item.metrics.average_speech_rate.toFixed(1)} 字/分鐘</p>
                              <p>能量平均值：{item.metrics.average_energy_mean.toFixed(2)}</p>
                            </div>
                          )}
                          {item.suggestions && (
                            <ul style={{ listStyleType: "disc", paddingLeft: "1.25rem", marginTop: "0.5rem" }}>
                              {item.suggestions.map((suggestion, i) => (
                                <li key={i}>{suggestion}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ) : null
                    )}
                    {stutterFeedback.map((item, index) =>
                      item.type === "summary" ? (
                        <div
                          key={`stutter-summary-${index}`}
                          style={{
                            padding: "0.5rem",
                            backgroundColor: "#F9FAFB",
                            borderRadius: "0.375rem",
                          }}
                        >
                          <h4 style={{ fontWeight: "500", marginBottom: "0.5rem" }}>
                            結疤總結
                          </h4>
                          <p>{item.message}</p>
                          <div style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
                            <p>口吃問題：{item.stutter_issues}</p>
                            <p>總段落數：{item.total_segments}</p>
                          </div>
                        </div>
                      ) : null
                    )}
                  </>
                )}

                {pitchFeedback.length === 0 && stutterFeedback.length === 0 && (
                  <p style={{ color: "#6B7280" }}>請上傳檔案或錄音以查看建議</p>
                )}
              </div>
            ) : (
              textSegments.length > 0 && textSegments[0].text !== "無轉錄內容可用" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {textSegments.map((segment, index) => (
                    <div
                      key={`transcription-${index}`}
                      style={{
                        padding: "0.5rem",
                        borderRadius: "0.375rem",
                        cursor: "pointer",
                        backgroundColor: "#F9FAFB",
                      }}
                      onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#F3F4F6")}
                      onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "#F9FAFB")}
                      onClick={() => handleTimeJump(segment.start_time)}
                    >
                      <p
                        style={{
                          fontWeight: "500",
                          color: needsImprovement(segment) ? "red" : "black",
                        }}
                      >
                        [{formatTime(segment.start_time)} - {formatTime(segment.end_time)}] {segment.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "#6B7280" }}>無轉錄內容可用</p>
              )
            )}
          </div>
        </div>

        {/* 音訊播放區塊 */}
        {audioUrl && !isProcessing && (
          <div
            style={{
              backgroundColor: "#EFF6FF",
              padding: "1rem",
              borderRadius: "0.5rem",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              border: "1px solid #BFDBFE",
              marginTop: "0.9rem",
              position: "relative",
            }}
          >
            <div style={{ position: "relative", width: "100%" }}>
              <audio
                ref={audioRef}
                src={audioUrl}
                controls
                style={{
                  width: "100%",
                  height: "40px",
                  "--progress-color": "#FFFFFF",
                }}
              />
              <style jsx>{`
                audio::-webkit-media-controls-current-time-display,
                audio::-webkit-media-controls-time-remaining-display {
                  color: #4B5563;
                }
                audio::-webkit-progress-bar {
                  background-color: #E5E7EB;
                }
                audio::-webkit-progress-value {
                  background-color: var(--progress-color);
                }
                audio::-moz-progress-bar {
                  background-color: var(--progress-color);
                }
              `}</style>
              <div
                style={{
                  position: "absolute",
                  top: "10px",
                  left: `${progressBarOffset}px`,
                  width: `${progressBarWidth}px`,
                  height: "10px",
                  pointerEvents: "none",
                  zIndex: 10,
                }}
              >
                {pitchFeedback
                  .filter((item) => item.type !== "summary")
                  .map((item, index) => (
                    <div
                      key={`pitch-${index}`}
                      style={{
                        position: "absolute",
                        left: getMarkerPosition(item.start_time),
                        top: "100%",
                        width: "12px",
                        height: "12px",
                        backgroundColor: item.severity === "high" ? "#EF4444" : "#F59E0B",
                        borderRadius: "50%",
                        transform: "translate(-50%, -50%)",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        border: "2px solid #ffffff",
                        zIndex: 11,
                      }}
                      onClick={() => handleTimeJump(item.start_time)}
                      title={`${item.text || ""} ${item.message || ""}`}
                    />
                  ))}
                {stutterFeedback
                  .filter((item) => item.type !== "summary")
                  .map((item, index) => (
                    <div
                      key={`stutter-${index}`}
                      style={{
                        position: "absolute",
                        left: getMarkerPosition(item.start_time),
                        top: "100%",
                        width: "12px",
                        height: "12px",
                        backgroundColor: "#3B82F6",
                        borderRadius: "50%",
                        transform: "translate(-50%, -50%)",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        border: "2px solid #ffffff",
                        zIndex: 11,
                      }}
                      onClick={() => handleTimeJump(item.start_time)}
                      title={`${item.text || ""} ${item.message || ""}`}
                    />
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}