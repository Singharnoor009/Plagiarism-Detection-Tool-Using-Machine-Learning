import React, { useState } from "react";
import "./styles/PlagiarismChecker.css";
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe("paymenttest_4BADN");

const PlagiarismChecker = () => {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isChecked, setIsChecked] = useState(false);
  const [reportUrl, setReportUrl] = useState("");
  const [alertMessage, setAlertMessage] = useState("");
  const [droppedFileName, setDroppedFileName] = useState("");

  const handleTextChange = (e) => {
    setText(e.target.value);
    setIsChecked(false);
    setAlertMessage("");
    setFile(null);
    setDroppedFileName("");
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setText("");
      setIsChecked(false);
      setAlertMessage("");
      setDroppedFileName("");
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setText("");
      setIsChecked(false);
      setAlertMessage("");
      setDroppedFileName(droppedFile.name);
    }
  };

  const clearFile = () => {
    setFile(null);
    setDroppedFileName("");
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.value = "";
  };

  const handlePlagiarismCheck = async () => {
    if (!text && !file) {
      setAlertMessage("Please provide text or upload a file.");
      return;
    }

    setLoading(true);
    setAlertMessage("");

    const formData = new FormData();

    if (text) {
      formData.append("text", text);
    } else if (file) {
      formData.append("file", file);
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/api/detect-plagiarism",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Network response was not ok. Status: ${response.status}. Message: ${errorText}`
        );
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      setReportUrl(url);
      setIsChecked(true);
    } catch (error) {
      console.error("Error checking plagiarism:", error);
      setAlertMessage(`An error occurred: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ cursor: loading ? "wait" : "default" }}>
      {/* Text Input Section */}
      <div>
        <textarea
          value={text}
          onChange={handleTextChange}
          placeholder="Enter text to check for plagiarism"
          disabled={loading || file}
        />
      </div>

      {/* File Upload Section */}
      <div>
        <label htmlFor="fileInput">
          Or choose a file to check for plagiarism:
        </label>
        <input
          type="file"
          id="fileInput"
          onChange={handleFileChange}
          accept=".pdf, .txt, .docx"
          disabled={loading || text}
        />
      </div>

      {/* Drag and Drop Section */}
      <div
        className="file-drop-zone"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{
          border: "2px dashed #ccc",
          padding: "20px",
          marginTop: "20px",
          cursor: "pointer",
          textAlign: "center",
        }}
      >
        <p>Drag & Drop your file here</p>
      </div>

      {/* Display Dropped File Name */}
      {droppedFileName && (
        <div className="file-name-display">
          <p>Dropped File: {droppedFileName}</p>
        </div>
      )}

      {/* File Name or Text Word Count */}
      <div className="word-count">
        {file
          ? `File: ${file.name}`
          : text
          ? `Word Count: ${
              text.split(/\s+/).filter((word) => word.length > 0).length
            }`
          : "No file or text selected"}
      </div>

      {/* Alert Message */}
      {alertMessage && (
        <div style={{ color: "red", marginTop: "10px" }}>{alertMessage}</div>
      )}

      {/* Check Button */}
      <button
        onClick={handlePlagiarismCheck}
        disabled={loading || (!text && !file)}
      >
        {loading ? "Checking..." : "Check Plagiarism"}
      </button>

      {/* Download Report Button */}
      {isChecked && (
        <div>
          <button>
            <a href={reportUrl} download="plagiarism_report.pdf">
              Download Report
            </a>
          </button>
        </div>
      )}

      {/* Clear File Button - Hidden when check is done or loading */}
      {file && !isChecked && !loading && (
        <button
          onClick={clearFile}
          style={{
            marginTop: "20px",
            backgroundColor: "#ff0000",
            color: "#fff",
          }}
        >
          Clear {droppedFileName ? "Dropped" : "Selected"} File
        </button>
      )}
    </div>
  );
};

export default PlagiarismChecker;
