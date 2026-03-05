import React, { useState } from "react";
import { uploadCSV } from "../api/client";

const UploadSection: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await uploadCSV(file);
      setSuccessMessage("Upload successful. You can now run queries.");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button
        onClick={handleUpload}
        disabled={!file || isUploading}
        style={{ marginLeft: "0.5rem" }}
      >
        {isUploading ? "Uploading..." : "Upload"}
      </button>
      {error && (
        <div style={{ color: "red", marginTop: "0.5rem" }}>{error}</div>
      )}
      {successMessage && !error && (
        <div style={{ color: "green", marginTop: "0.5rem" }}>
          {successMessage}
        </div>
      )}
    </div>
  );
};

export default UploadSection;
