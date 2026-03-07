import { useState } from "react";
import { Button, Stack, TextField, Typography } from "@mui/material";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";

interface Props {
  onSubmit: (query: string) => void;
  disabled?: boolean;
}

const QuerySection = ({ onSubmit, disabled = false }: Props) => {
  const [query, setQuery] = useState<string>("");

  const handleSubmit = () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle1" fontWeight={700}>
        Ask a question
      </Typography>
      <TextField
        multiline
        minRows={3}
        maxRows={6}
        fullWidth
        value={query}
        placeholder="Ask a question about your data..."
        onChange={(e) => setQuery(e.target.value)}
        disabled={disabled}
        helperText="Examples: top 10 customers by revenue, monthly sales trend, average order value by region."
      />
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={disabled || !query.trim()}
        startIcon={<AutoAwesomeRoundedIcon />}
        sx={{ alignSelf: "flex-start" }}
      >
        Run AI query
      </Button>
    </Stack>
  );
};

export default QuerySection;
