import { List, ListItem, ListItemText, Typography } from "@mui/material";

interface Props {
  insights: string;
}

const InsightsPanel = ({ insights }: Props) => {
  if (!insights) return null;

  const items = insights
    .split(/\n+/)
    .map((item) => item.replace(/^[\-\*\d\.\s]+/, "").trim())
    .filter(Boolean);

  return (
    <>
      <Typography variant="h6" gutterBottom>
        Insights
      </Typography>
      {items.length > 1 ? (
        <List dense sx={{ p: 0 }}>
          {items.map((item) => (
            <ListItem key={item} sx={{ px: 0 }}>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="text.secondary">
          {insights}
        </Typography>
      )}
    </>
  );
};

export default InsightsPanel;
