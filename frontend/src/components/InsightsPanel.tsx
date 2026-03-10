import { List, ListItem, ListItemText, Typography } from "@mui/material";

interface Props {
  insights: string;
}

const InsightsPanel = ({ insights }: Props) => {
  if (!insights) return null;

  const items = insights // "1. This is a test\n2. So let it begin\n3. Test done"
    .split(/\n+/) // ["1. This is a test", "2. So let it begin", "3. Test done"]
    .map((item) => item.replace(/^[\-\*\d\.\s]+/, "").trim()) // ["This is a test", "So let it begin", "Test done"]
    .filter(Boolean); // ["This is a test", "So let it begin", "Test done"]

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
          {insights} {/* This is a test - if i recieved insights = "This is a test" */} 
        </Typography>
      )}
    </>
  );
};

export default InsightsPanel;
