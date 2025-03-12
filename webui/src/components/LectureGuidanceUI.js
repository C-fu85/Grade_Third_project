import { useState, useEffect, useRef } from "react";

export default function LectureGuidanceUI() {
  const [textSegments, setTextSegments] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [fileName, setFileName] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const timelineRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const transcribeResponse = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!transcribeResponse.ok) {
        const errorData = await transcribeResponse.json();
        throw new Error(errorData.error || "Transcription failed");
      }

      const transcribeData = await transcribeResponse.json();
      console.log("Received data:", transcribeData);
      if (transcribeData.feedback) {
        const segments = transcribeData.feedback
          .filter((item) => item.type !== "summary")
          .map((item) => ({
            text: item.text || "",
            start_time: item.start_time || 0,
            end_time: item.end_time || 0,
            segment_index: item.segment_index || 0,
          }));
        setTextSegments(segments);
        setFeedback(transcribeData.feedback);
        setCurrentTime(0);
      } else {
        setTextSegments([{ text: "No transcription available", start_time: 0, end_time: 0 }]);
        setFeedback([]);
      }
    } catch (error) {
      console.error("Error processing file:", error);
      setTextSegments([{ text: "Error processing file: " + error.message, start_time: 0, end_time: 0 }]);
      setFeedback([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTime = (seconds) => {
    const numSeconds = Number(seconds) || 0;
    const minutes = Math.floor(numSeconds / 60);
    const secs = Math.floor(numSeconds % 60);
    return `${minutes}:${secs < 10 ? "0" + secs : secs}`;
  };

  const totalDuration = feedback.length > 0
    ? Math.max(
        ...feedback
          .filter((item) => item.end_time !== undefined && !isNaN(item.end_time))
          .map((item) => Number(item.end_time))
      ) || 378 // 預設值 378 秒
    : 378; // 預設值 378 秒
  console.log("Total Duration:", totalDuration);

  const handleSliderChange = (e) => {
    setCurrentTime(Number(e.target.value));
  };

  const handleMarkerClick = (startTime) => {
    setCurrentTime(startTime);
  };

  const currentSegment = textSegments.find(
    (segment) => currentTime >= segment.start_time && currentTime <= segment.end_time
  );

  const currentFeedback = feedback.find(
    (item) =>
      item.type !== "summary" &&
      currentTime >= item.start_time &&
      currentTime <= item.end_time
  );

  const getMarkerPosition = (time) => {
    if (totalDuration === 0) return "0%";
    return `${(time / totalDuration) * 100}%`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex p-6">
      <div className="w-full pr-6">
        <h1 className="text-2xl font-bold mb-4">Lecture Guidance System</h1>

        <div className="mb-4">
          <label className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg cursor-pointer">
            <span>{isProcessing ? "Processing..." : "Upload File"}</span>
            <input
              type="file"
              className="hidden"
              accept=".mp3,.mp4,.wav,.m4a"
              onChange={handleFileUpload}
              disabled={isProcessing}
            />
          </label>
          {fileName && (
            <span className="ml-4 text-gray-400 text-sm">Selected: {fileName}</span>
          )}
        </div>

        {/* 時間條 */}
        <div className="mb-4">
          <div className="relative w-full h-6 bg-gray-300 rounded-full">
            {/* 底色和進度條 */}
            <div className="absolute top-0 left-0 h-full bg-gray-300 rounded-full">
              <div
                className="h-full bg-red-500 rounded-full transition-all duration-200"
                style={{ width: `calc(${(currentTime / totalDuration) * 100}%)` }}
              />
            </div>

            {/* 建議標記 */}
            {feedback
              .filter((item) => item.type !== "summary" && item.severity)
              .map((item, index) => (
                <div
                  key={index}
                  className={`absolute h-8 w-8 rounded-full ${
                    item.severity === "high" ? "bg-red-500" : "bg-yellow-500"
                  } transform -translate-x-1/2 -translate-y-1/2 top-1/2 z-10 cursor-pointer`}
                  style={{ left: getMarkerPosition(item.start_time) }}
                  onClick={() => handleMarkerClick(item.start_time)}
                  title={`${item.text} (${item.message})`}
                />
              ))}

            {/* 時間滑塊 */}
            <input
              type="range"
              min="0"
              max={totalDuration}
              value={currentTime}
              onChange={handleSliderChange}
              className="absolute w-full h-full top-0 cursor-pointer opacity-0 z-0"
              style={{ background: "transparent" }}
            />
          </div>
          <p className="text-center text-gray-400 mt-2 mb-4">
            {`${formatTime(currentTime)} / ${formatTime(totalDuration)}`}
          </p>

          {/* Suggestions 區移到時間條下方 */}
          {feedback.length > 0 && (
            <div className="bg-gray-800 p-4 rounded-lg mb-4">
              <h2 className="text-xl font-semibold mb-2">Suggestions</h2>
              <div className="max-h-40 overflow-y-auto">
                {currentFeedback ? (
                  <div className="mt-2 p-2 bg-gray-700 rounded">
                    <p>
                      Segment {currentFeedback.segment_index} [
                      {formatTime(currentFeedback.start_time)} -{" "}
                      {formatTime(currentFeedback.end_time)}]: {currentFeedback.text}
                    </p>
                    <p
                      className={`text-${
                        currentFeedback.severity === "high" ? "red" : "yellow"
                      }-400`}
                    >
                      {currentFeedback.message}
                    </p>
                  </div>
                ) : (
                  <p className="text-gray-400">No feedback for current time</p>
                )}
                {feedback.map((item, index) =>
                  item.type === "summary" ? (
                    <div key={index} className="mt-4 p-2 bg-gray-700 rounded">
                      <h3 className="font-semibold">Summary</h3>
                      <p>{item.message}</p>
                    </div>
                  ) : null
                )}
              </div>
            </div>
          )}
        </div>

        {/* 時間表 */}
        {textSegments.length > 0 && (
          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">Transcription Timeline</h2>
            <div className="max-h-96 overflow-y-auto">
              {textSegments.map((segment, index) => {
                const hasFeedback = feedback.some(
                  (item) => item.segment_index === segment.segment_index && item.type !== "summary"
                );
                const isActive = currentSegment && currentSegment.segment_index === segment.segment_index;
                return (
                  <div
                    key={index}
                    className={`p-2 mb-2 rounded ${
                      hasFeedback ? "bg-yellow-900" : "bg-gray-700"
                    } ${isActive ? "border-2 border-blue-500" : ""}`}
                  >
                    <span className="text-gray-400">
                      [{formatTime(segment.start_time)} - {formatTime(segment.end_time)}]
                    </span>{" "}
                    {segment.text}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}