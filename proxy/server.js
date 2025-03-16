const express = require("express");
const axios = require("axios");
const fileUpload = require("express-fileupload");
const FormData = require("form-data");

const app = express();

// Increase payload limits
app.use(express.json({ limit: "50mb" })); // For JSON payloads
app.use(express.urlencoded({ limit: "50mb", extended: true })); // For URL-encoded payloads
app.use(fileUpload({ limits: { fileSize: 200 * 1024 * 1024 } })); // 200MB limit for file uploads

const PYTHON_API_URL = "http://localhost:5000";

app.post("/api/transcribe", async (req, res) => {
  try {
    if (!req.files || !req.files.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }

    const file = req.files.file;
    const formData = new FormData();
    formData.append("file", file.data, {
      filename: file.name,
      contentType: file.mimetype,
    });

    // 從 URL 查詢參數中獲取性別並添加到請求 URL
    const gender = req.query.gender;
    const url = `${PYTHON_API_URL}/api/transcribe${gender ? `?gender=${gender}` : ''}`;
    console.log("Forwarding to URL:", url); // 調試用

    const response = await axios.post(url, formData, {
      headers: formData.getHeaders(),
    });

    res.json(response.data);
  } catch (error) {
    console.error("Transcription error:", error);
    res.status(500).json({ error: "Transcription failed" });
  }
});

app.post("/api/analyze-speech", async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/api/analyze`, req.body, {
      headers: { "Content-Type": "application/json" },
    });
    res.json(response.data);
  } catch (error) {
    console.error("Analysis error:", error);
    res.status(500).json({ error: "Analysis failed" });
  }
});

const PORT = 4000;
app.listen(PORT, () => console.log(`Node.js proxy running on port ${PORT}`));