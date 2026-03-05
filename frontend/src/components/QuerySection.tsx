import { useState } from "react";

interface Props {
  onSubmit: (query: string) => void;
}

const QuerySection = ({ onSubmit }: Props) => {
  const [query, setQuery] = useState<string>("");

  return (
    <div>
      <input
        type="text"
        value={query}
        placeholder="Ask a question about your data..."
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={() => onSubmit(query)}>Run</button>
    </div>
  );
};

export default QuerySection;
