import React, { useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import CloudUploadRoundedIcon from "@mui/icons-material/CloudUploadRounded";
import { uploadCSV } from "../api/client";
import type { UploadResponse } from "../types/api";

interface UploadSectionProps {
  onUploadSuccess?: (response: UploadResponse) => void;
}

const UploadSection: React.FC<UploadSectionProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await uploadCSV(file);
      onUploadSuccess?.(response);
      setSuccessMessage(
        `Uploaded ${response.row_count.toLocaleString()} rows successfully.`,
      );
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Stack spacing={2}>
      <Box
        sx={{
          p: 2,
          borderRadius: 3,
          border: "1px dashed",
          borderColor: "divider",
          bgcolor: "background.default",
        }}
      >
        <Stack spacing={1.5}>
          <Typography variant="subtitle1" fontWeight={700}>
            Upload a CSV dataset
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Start with a clean CSV file. The dataset loads into DuckDB so you can
            query it immediately in plain English.
          </Typography>
          <input
            ref={inputRef}
            hidden
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
            <Button
              variant="outlined"
              startIcon={<CloudUploadRoundedIcon />}
              onClick={() => inputRef.current?.click()}
            >
              Choose CSV
            </Button>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!file || isUploading}
            >
              {isUploading ? (
                <Stack direction="row" spacing={1} alignItems="center">
                  <CircularProgress size={18} color="inherit" />
                  <span>Uploading</span>
                </Stack>
              ) : (
                "Upload dataset"
              )}
            </Button>
          </Stack>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <Chip
              label={file ? `Selected: ${file.name}` : "No file selected"}
              color={file ? "primary" : "default"}
              variant={file ? "filled" : "outlined"}
            />
          </Stack>
        </Stack>
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      {successMessage && !error && <Alert severity="success">{successMessage}</Alert>}
    </Stack>
  );
};

export default UploadSection;
