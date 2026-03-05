interface Props {
  chartHtml: string;
}

const ChartView = ({ chartHtml }: Props) => {
  if (!chartHtml) return null;

  return <div dangerouslySetInnerHTML={{ __html: chartHtml }} />;
};

export default ChartView;
