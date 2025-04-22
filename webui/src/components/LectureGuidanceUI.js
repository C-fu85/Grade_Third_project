import { useState, useRef, useEffect } from "react";
import React from "react";
import {
  Sun,
  Moon,
  UploadCloud,
  Mic,
  Play,
  Pause,
  StopCircle,
  CheckCircle,
  XCircle,
  List,
  FileText,
} from "lucide-react";

export default function LectureGuidanceSystem() {
  // 狀態管理
  const [textSegments, setTextSegments] = useState([]);
  const [pitchFeedback, setPitchFeedback] = useState([]);
  const [stutterFeedback, setStutterFeedback] = useState([]);
  const [fileName, setFileName] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [style, setStyle] = useState("default");
  const [speed, setSpeed] = useState("standard");
  const [audioUrl, setAudioUrl] = useState(null);
  const [viewMode, setViewMode] = useState("Feedback");
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showConfirm, setShowConfirm] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [darkMode, setDarkMode] = useState(false);

  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const [progressBarOffset, setProgressBarOffset] = useState(0);
  const [progressBarWidth, setProgressBarWidth] = useState(0);

  //Dark mode switch
  const theme = {
    container: darkMode
      ? { background: "#1F2937", color: "#D1D5DB" }
      : {
          background: "linear-gradient(to bottom, #e0f7fa, #ffffff)",
          color: "#1F2937",
        },
    panel: darkMode
      ? {
          backgroundColor: "#374151",
          color: "#D1D5DB",
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.5)",
        }
      : {
          backgroundColor: "#ffffff",
          color: "#4B5563",
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
        },
    accent: "#3B82F6",
    text: darkMode ? "#D1D5DB" : "#1F2937",
    subText: darkMode ? "#9CA3AF" : "#6B7280",
    border: darkMode ? "#4B5563" : "#E5E7EB",
  };
  // 處理檔案上傳
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

    // 修改 API 請求，加入 speed 參數
    const url = `/api/transcribe?style=${encodeURIComponent(
      style
    )}&speed=${encodeURIComponent(speed)}`;

    try {
      const res = await fetch(url, { method: "POST", body: formData });
      if (!res.ok) throw new Error((await res.json()).error || "轉錄失敗");
      const data = await res.json();
      setTextSegments(
        data.transcriptions || [
          { text: "無轉錄內容可用", start_time: 0, end_time: 0 },
        ]
      );
      setPitchFeedback(data.pitch_feedback || []);
      setStutterFeedback(data.stutter_feedback || []);
      setAudioUrl(URL.createObjectURL(file));
    } catch (error) {
      console.error(error);
      setTextSegments([
        {
          text: "處理檔案時發生錯誤: " + error.message,
          start_time: 0,
          end_time: 0,
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  // 錄音相關
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) =>
        audioChunksRef.current.push(e.data);
      mediaRecorderRef.current.onstop = handleRecordingStop;
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);
      setFileName("錄音中...");
      timerRef.current = setInterval(
        () => setRecordingTime((t) => t + 1),
        1000
      );
    } catch {
      alert("無法開始錄音，請確認麥克風權限");
    }
  };

  // 暫停錄音
  const pauseRecording = () => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      clearInterval(timerRef.current);
    }
  };

  // 恢復錄音
  const resumeRecording = () => {
    if (mediaRecorderRef.current?.state === "paused") {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      timerRef.current = setInterval(
        () => setRecordingTime((t) => t + 1),
        1000
      );
    }
  };

  // 停止錄音
  const handleRecordingStop = () => {
    const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
    setRecordedBlob(blob);
    setIsRecording(false);
    setIsPaused(false);
    setShowConfirm(true);
    clearInterval(timerRef.current);
    mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
    setFileName(`錄音完成 (${recordingTime} 秒)`);
  };

  // 確認上傳錄音
  const confirmUpload = async () => {
    if (!recordedBlob) return;
    setShowConfirm(false);
    setIsProcessing(true);
    const file = new File([recordedBlob], "recording.wav", {
      type: "audio/wav",
    });
    setFileName(file.name);
    const formData = new FormData();
    formData.append("file", file);

    // 修改 API 請求，加入 speed 參數
    const url = `/api/transcribe?style=${encodeURIComponent(
      style
    )}&speed=${encodeURIComponent(speed)}`;

    try {
      const res = await fetch(url, { method: "POST", body: formData });
      if (!res.ok) throw new Error((await res.json()).error || "轉錄失敗");
      const data = await res.json();
      setTextSegments(data.transcriptions || []);
      setPitchFeedback(data.pitch_feedback || []);
      setStutterFeedback(data.stutter_feedback || []);
      setAudioUrl(URL.createObjectURL(file));
    } catch (error) {
      console.error(error);
      setTextSegments([
        {
          text: "處理錄音時發生錯誤: " + error.message,
          start_time: 0,
          end_time: 0,
        },
      ]);
    } finally {
      setIsProcessing(false);
      setRecordedBlob(null);
    }
  };

  // 取消上傳
  const cancelUpload = () => {
    setShowConfirm(false);
    setRecordedBlob(null);
    setFileName("");
    setRecordingTime(0);
  };

  // 監聽音訊播放時間與進度條尺寸
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => setCurrentTime(audio.currentTime);
    audio.addEventListener("timeupdate", onTime);
    const calcBounds = () => {
      const rect = audio.getBoundingClientRect();
      const left = 120,
        right = 100;
      setProgressBarOffset(left);
      setProgressBarWidth(rect.width - left - right);
    };
    audio.addEventListener("loadedmetadata", calcBounds);
    window.addEventListener("resize", calcBounds);
    calcBounds();
    return () => {
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("loadedmetadata", calcBounds);
      window.removeEventListener("resize", calcBounds);
    };
  }, [audioUrl]);

  // 清理
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [audioUrl]);

  // 格式化時間
  const formatTime = (s) => {
    const secs = Math.floor(s || 0);
    const m = Math.floor(secs / 60);
    const ss = secs % 60;
    return `${m}:${ss < 10 ? "0" + ss : ss}`;
  };

  // 使用錄音時間作為總時長（如果有錄音），否則使用 textSegments 的最大 end_time
  const totalDuration =
    audioUrl && recordedBlob
      ? recordingTime
      : textSegments.length
      ? Math.max(...textSegments.map((it) => Number(it.end_time) || 0), 1)
      : 0;
  const handleTimeJump = (t) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, t - 1);
      audioRef.current.play();
    }
  };
  const getMarkerPosition = (t) =>
    totalDuration && progressBarWidth ? `${(t / totalDuration) * 100}%` : "0%";

  // 修改 needsImprovement 函數，返回具體的問題類型
  const needsImprovement = (seg) => {
    const start = Number(seg.start_time),
      end = Number(seg.end_time);
    const hasStutter = stutterFeedback.some(
      (f) => f.type !== "summary" && start <= f.end_time && end >= f.start_time
    );
    const hasPitch = pitchFeedback.some(
      (f) => f.type !== "summary" && start <= f.end_time && end >= f.start_time
    );
    if (hasStutter && hasPitch) return "both";
    if (hasStutter) return "stutter";
    if (hasPitch) return "pitch";
    return "none";
  };

  const getSortedFeedback = () =>
    [
      ...pitchFeedback
        .filter((f) => f.type !== "summary")
        .map((f) => ({ ...f, feedbackType: "pitch" })),
      ...stutterFeedback
        .filter((f) => f.type !== "summary")
        .map((f) => ({ ...f, feedbackType: "stutter" })),
    ].sort((a, b) => {
      const d = a.start_time - b.start_time;
      return d !== 0 ? d : a.feedbackType === "pitch" ? -1 : 1;
    });

  return (
    <div
      style={{
        padding: "1.5rem",
        minHeight: "100vh",
        boxSizing: "border-box",
        ...theme.container,
      }}
    >
      <div style={{ maxWidth: "84rem", margin: "0 auto" }}>
        {/* Dark Mode 切換 */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            marginBottom: "1rem",
          }}
        >
          <button
            onClick={() => setDarkMode((d) => !d)}
            style={{
              padding: "0.5rem 1rem",
              backgroundColor: theme.accent,
              color: "#fff",
              border: "none",
              borderRadius: "0.375rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              cursor: "pointer",
            }}
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

        <div style={{ display: "flex", gap: "0.9rem", marginBottom: "0.9rem" }}>
          {/* 上傳與分析 區塊 */}
          <div
            style={{
              width: "33.333%",
              minHeight: "400px",
              padding: "1.5rem",
              borderRadius: "0.5rem",
              ...theme.panel,
              position: "relative",
            }}
          >
            <h2
              style={{
                fontSize: "1.25rem",
                fontWeight: 600,
                marginBottom: "1rem",
                color: theme.text,
              }}
            >
              上傳與分析
            </h2>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
            >
              <div>
                <label
                  htmlFor="style"
                  style={{
                    display: "block",
                    color: theme.subText,
                    marginBottom: "0.25rem",
                  }}
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
                    border: `1px solid ${theme.border}`,
                    borderRadius: "0.375rem",
                  }}
                >
                  <option value="default">預設</option>
                  <option value="passionate">熱情</option>
                </select>
              </div>
              <div>
                <label
                  htmlFor="speed"
                  style={{
                    display: "block",
                    color: theme.subText,
                    marginBottom: "0.25rem",
                  }}
                >
                  語速：
                </label>
                <select
                  id="speed"
                  value={speed}
                  onChange={(e) => setSpeed(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: `1px solid ${theme.border}`,
                    borderRadius: "0.375rem",
                  }}
                >
                  <option value="standard">標準</option>
                  <option value="slow">慢</option>
                  <option value="fast">快</option>
                </select>
              </div>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.5rem",
                  width: "400px",
                  padding: "0.5rem",
                  backgroundColor: theme.accent,
                  color: "#fff",
                  textAlign: "center",
                  borderRadius: "0.375rem",
                  cursor:
                    isProcessing || isRecording ? "not-allowed" : "pointer",
                }}
              >
                <UploadCloud size={16} />
                <span>{isProcessing ? "處理中..." : "上傳檔案"}</span>
                <input
                  type="file"
                  style={{ display: "none" }}
                  accept=".mp3,.mp4,.wav,.m4a"
                  onChange={handleFileUpload}
                  disabled={isProcessing || isRecording}
                />
              </label>

              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  onClick={
                    isProcessing
                      ? undefined
                      : isRecording
                      ? isPaused
                        ? resumeRecording
                        : pauseRecording
                      : startRecording
                  }
                  disabled={isProcessing}
                  style={{
                    flex: 1,
                    padding: "0.5rem",
                    backgroundColor: isProcessing
                      ? "#6B7280"
                      : isRecording
                      ? isPaused
                        ? "#F59E0B"
                        : "#EF4444"
                      : "#10B981",
                    color: "#fff",
                    borderRadius: "0.375rem",
                    border: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.5rem",
                    cursor: isProcessing ? "not-allowed" : "pointer",
                  }}
                >
                  {isProcessing ? (
                    "處理中..."
                  ) : isRecording ? (
                    isPaused ? (
                      <>
                        <Play size={16} />
                        恢復錄音
                      </>
                    ) : (
                      <>
                        <Pause size={16} />
                        暫停錄音
                      </>
                    )
                  ) : (
                    <>
                      <Mic size={16} />
                      開始錄音
                    </>
                  )}
                </button>
                {isRecording && (
                  <button
                    onClick={() => mediaRecorderRef.current?.stop()}
                    style={{
                      flex: 1,
                      padding: "0.5rem",
                      backgroundColor: "#EF4444",
                      color: "#fff",
                      borderRadius: "0.375rem",
                      border: "none",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.5rem",
                      cursor: "pointer",
                    }}
                  >
                    <StopCircle size={16} />
                    停止錄音
                  </button>
                )}
              </div>

              {isRecording && (
                <p style={{ color: theme.subText }}>
                  錄音時間：{formatTime(recordingTime)}
                </p>
              )}
              {fileName && !isRecording && (
                <p style={{ color: theme.subText }}>已選擇：{fileName}</p>
              )}
              {isProcessing && (
                <p style={{ color: theme.subText }}>正在處理您的檔案...</p>
              )}
            </div>

            {showConfirm && (
              <div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  ...theme.panel,
                  zIndex: 20,
                }}
              >
                <p style={{ marginBottom: "1rem", color: theme.text }}>
                  是否要上傳這段錄音（{formatTime(recordingTime)}）？
                </p>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={confirmUpload}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#10B981",
                      color: "#fff",
                      border: "none",
                      borderRadius: "0.375rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      cursor: "pointer",
                    }}
                  >
                    <CheckCircle size={16} />是
                  </button>
                  <button
                    onClick={cancelUpload}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#EF4444",
                      color: "#fff",
                      border: "none",
                      borderRadius: "0.375rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      cursor: "pointer",
                    }}
                  >
                    <XCircle size={16} />否
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 大綱與建議 區塊 */}
          <div
            style={{
              width: "66.667%",
              minHeight: "400px",
              padding: "0 1.5rem 1.5rem 1.5rem",
              borderRadius: "0.5rem",
              ...theme.panel,
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
                top: "0",
                backgroundColor: theme.panel.backgroundColor,
                padding: "1.5rem 0 0.5rem",
                borderBottom: `1px solid ${theme.border}`,
                zIndex: 10,
              }}
            >
              <h2
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 600,
                  color: theme.text,
                }}
              >
                大綱與建議
              </h2>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button
                  onClick={() => setViewMode("Feedback")}
                  style={{
                    padding: "0.25rem 0.75rem",
                    borderRadius: "0.375rem",
                    backgroundColor:
                      viewMode === "Feedback"
                        ? theme.accent
                        : theme.panel.backgroundColor,
                    color: viewMode === "Feedback" ? "#fff" : theme.text,
                    border: `1px solid ${theme.border}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    cursor: "pointer",
                  }}
                >
                  <List size={14} />
                  建議
                </button>
                <button
                  onClick={() => setViewMode("Transcriptions")}
                  style={{
                    padding: "0.25rem 0.75rem",
                    borderRadius: "0.375rem",
                    backgroundColor:
                      viewMode === "Transcriptions"
                        ? theme.accent
                        : theme.panel.backgroundColor,
                    color: viewMode === "Transcriptions" ? "#fff" : theme.text,
                    border: `1px solid ${theme.border}`,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    cursor: "pointer",
                  }}
                >
                  <FileText size={14} />
                  字幕
                </button>
              </div>
            </div>

            {viewMode === "Feedback" ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                {pitchFeedback.length + stutterFeedback.length > 0 ? (
                  getSortedFeedback().map((item, idx) => {
                    const bg = darkMode ? "#4B5563" : "#F9FAFB";
                    const hover = darkMode ? "#6B7280" : "#F3F4F6";
                    const color =
                      item.feedbackType === "pitch"
                        ? item.severity === "high"
                          ? "#EF4444"
                          : "#F59E0B"
                        : "#3B82F6";
                    return (
                      <div
                        key={idx}
                        onClick={() => handleTimeJump(item.start_time)}
                        style={{
                          padding: "0.25rem",
                          borderRadius: "0.375rem",
                          backgroundColor: bg,
                          color: theme.text,
                          cursor: "pointer",
                        }}
                        onMouseOver={(e) =>
                          (e.currentTarget.style.backgroundColor = hover)
                        }
                        onMouseOut={(e) =>
                          (e.currentTarget.style.backgroundColor = bg)
                        }
                      >
                        <p style={{ fontWeight: 500 }}>
                          [{formatTime(item.start_time)} -{" "}
                          {formatTime(item.end_time)}] {item.text}
                        </p>
                        <p style={{ color }}>{item.message}</p>
                      </div>
                    );
                  })
                ) : (
                  <p style={{ color: theme.subText }}>
                    請上傳檔案或錄音以查看建議
                  </p>
                )}
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                {textSegments.map((seg, i) => {
                  const imp = needsImprovement(seg);
                  const col =
                    imp === "both"
                      ? "#EF4444"
                      : imp === "stutter"
                      ? "#3B82F6"
                      : imp === "pitch"
                      ? "#F59E0B"
                      : theme.text;
                  const bg = darkMode ? "#4B5563" : "#F9FAFB";
                  const hover = darkMode ? "#6B7280" : "#F3F4F6";
                  return (
                    <div
                      key={i}
                      onClick={() => handleTimeJump(seg.start_time)}
                      style={{
                        padding: "0.5rem",
                        borderRadius: "0.375rem",
                        backgroundColor: bg,
                        cursor: "pointer",
                      }}
                      onMouseOver={(e) =>
                        (e.currentTarget.style.backgroundColor = hover)
                      }
                      onMouseOut={(e) =>
                        (e.currentTarget.style.backgroundColor = bg)
                      }
                    >
                      <p style={{ fontWeight: 500, color: col }}>
                        [{formatTime(seg.start_time)} -{" "}
                        {formatTime(seg.end_time)}] {seg.text}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* 音訊播放 區塊 */}
        {audioUrl && !isProcessing && (
          <div
            style={{
              padding: "1rem",
              borderRadius: "0.5rem",
              border: `1px solid ${theme.border}`,
              marginTop: "0.9rem",
              position: "relative",
              ...theme.panel,
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
                  "--progress-color": "#fff",
                }}
              />
              <style jsx>{`
                audio::-webkit-media-controls-current-time-display,
                audio::-webkit-media-controls-time-remaining-display {
                  color: ${theme.text};
                }
                audio::-webkit-progress-bar {
                  background-color: ${darkMode ? "#4B5563" : "#e5e7eb"};
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
                  left: progressBarOffset,
                  width: progressBarWidth,
                  height: "10px",
                  pointerEvents: "none",
                  zIndex: 10,
                }}
              >
                {pitchFeedback
                  .filter((it) => it.type !== "summary")
                  .map((it, i) => (
                    <div
                      key={`p${i}`}
                      onClick={() => handleTimeJump(it.start_time)}
                      title={`${it.text} ${it.message}`}
                      style={{
                        position: "absolute",
                        left: getMarkerPosition(it.start_time),
                        top: "100%",
                        width: "12px",
                        height: "12px",
                        backgroundColor:
                          it.severity === "high" ? "#EF4444" : "#F59E0B",
                        borderRadius: "50%",
                        transform: "translate(-50%, -50%)",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        border: "2px solid #fff",
                        zIndex: 11,
                      }}
                    />
                  ))}
                {stutterFeedback
                  .filter((it) => it.type !== "summary")
                  .map((it, i) => (
                    <div
                      key={`s${i}`}
                      onClick={() => handleTimeJump(it.start_time)}
                      title={`${it.text} ${it.message}`}
                      style={{
                        position: "absolute",
                        left: getMarkerPosition(it.start_time),
                        top: "100%",
                        width: "12px",
                        height: "12px",
                        backgroundColor: "#3B82F6",
                        borderRadius: "50%",
                        transform: "translate(-50%, -50%)",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        border: "2px solid #fff",
                        zIndex: 11,
                      }}
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
