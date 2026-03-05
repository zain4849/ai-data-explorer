interface Props {
  insights: string;
}

const InsightsPanel = ({ insights }: Props) => {
  if (!insights) return null;

    return <>
        <h3>Insights</h3>
        <p>{insights}</p>
    </>
};

export default InsightsPanel;
