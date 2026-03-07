import { Box } from "@mui/material";

interface Props {
  chartHtml: string;
}

const ChartView = ({ chartHtml }: Props) => {
  if (!chartHtml) return null;

  return (
    <Box
      sx={{
        "& > div": {
          width: "100%",
        },
      }}
      dangerouslySetInnerHTML={{ __html: chartHtml }}
    />
  );
};

export default ChartView;
