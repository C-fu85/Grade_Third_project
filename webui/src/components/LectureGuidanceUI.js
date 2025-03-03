import { useState } from "react";

export default function LectureGuidanceUI() {
  const [text, setText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [fileName, setFileName] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", file); // Append the file to FormData

    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData, // Send FormData with the file
      });

      if (!response.ok) {
        throw new Error("Transcription failed");
      }

      const data = await response.json();
      if (data.segments) {
        // Extract text from segments and set it
        const segmentText = Object.values(data.segments)
          .map((s) => s.results.text)
          .join(" ");
        setText(segmentText);

        // Send cache data for pitch analysis
        const analysisResponse = await fetch("/api/analyze-speech", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cache_data: data.segments }),
        });

        if (!analysisResponse.ok) {
          throw new Error("Analysis failed");
        }

        const analysisData = await analysisResponse.json();
        setAnalysis(analysisData);
      } else {
        setText("No transcription available");
      }
    } catch (error) {
      console.error("Error uploading file:", error);
      setText("Error processing file: " + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAnalyze = async () => {
    if (!text) return;

    setIsProcessing(true);
    try {
      const response = await fetch("/api/analyze-speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }), // For manual text input (if needed)
      });

      if (!response.ok) {
        throw new Error("Analysis failed");
      }

      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center p-6">
      <h1 className="text-2xl font-bold mb-4">Lecture Guidance System</h1>

      <div className="w-full max-w-2xl">
        <textarea
          className="w-full p-3 bg-gray-800 text-white rounded-lg mb-4"
          rows="6"
          placeholder="Enter your speech here or upload an audio/video file below..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isProcessing}
        ></textarea>

        <div className="flex items-center gap-4">
          <label className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg cursor-pointer">
            <span>{isProcessing ? "Processing..." : "Upload File"}</span>
            <input
              type="file"
              className="hidden"
              accept=".mp3,.mp4,.wav" // Adjust based on supported types
              onChange={handleFileUpload}
              disabled={isProcessing}
            />
          </label>
          {fileName && (
            <span className="text-gray-400 text-sm">Selected: {fileName}</span>
          )}
        </div>
      </div>

      <button
        className="mt-4 px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50"
        onClick={handleAnalyze}
        disabled={isProcessing || !text}
      >
        Analyze Speech
      </button>

      {analysis && (
        <div className="mt-6 w-full max-w-2xl bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl font-semibold">Analysis Results</h2>
          {analysis.feedback && analysis.feedback.map((item, index) => (
            <div key={index} className="mt-2 p-2 bg-gray-700 rounded">
              {item.type === "summary" ? (
                <div>
                  <h3 className="font-semibold">Summary</h3>
                  <p>{item.message}</p>
                </div>
              ) : (
                <>
                  <p>Segment {item.segment_index}: {item.text}</p>
                  <p className={`text-${item.severity === 'high' ? 'red' : 'yellow'}-400`}>
                    {item.message}
                  </p>
                  <p className="text-gray-500 text-sm">{item.timestamp}</p>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}