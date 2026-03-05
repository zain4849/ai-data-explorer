import React, { useState } from "react";
import { uploadCSV } from "../api/client";

interface Props {
  onUploadSuccess: (columns: string[]) => void;
}

const UploadSection = () => {
  const [file, setFile] = useState<File | null>(null);

  const handleUpload = async () => {
    if (!file) return

    try {
        const data = await uploadCSV(file) 
        // onUploadSuccess(data) // data here is the parsed array
        alert("Upload succesful")
    } catch (err) {
        alert(`Upload failed ${err}`)
    }
  }

  return (
    <div>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      /> {/* ? returns undefined instead of crashing in case of user cancels */}
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
};

export default UploadSection;
