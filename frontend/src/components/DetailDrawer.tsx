// src/components/DetailDrawer.tsx
import React, { useState, useEffect } from "react";
import {
  Drawer,
  Box,
  IconButton,
  Typography,
  Chip,
  Button,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import TagEditor from "./TagEditor";
import { fetchItemDetail } from "../utils/api";
import type { ExplorerItem } from "../utils/api";

interface DetailDrawerProps {
  open: boolean;
  itemId: string | null;
  onClose: () => void;
}

const DetailDrawer: React.FC<DetailDrawerProps> = ({
  open,
  itemId,
  onClose,
}) => {
  const [item, setItem] = useState<ExplorerItem | null>(null);

  useEffect(() => {
    if (itemId) {
      fetchItemDetail(itemId).then(setItem).catch(console.error);
    }
  }, [itemId]);

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box width={400} p={2}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{item?.title}</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>

        {item && (
          <>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {new Date(item.date).toLocaleDateString()} • {item.platform}
            </Typography>

            <Box mb={2}>
              <Typography variant="body1">{item.description}</Typography>
            </Box>

            {item.speakers && (
              <Box mb={2} display="flex" flexWrap="wrap" gap={1}>
                {item.speakers.map((s) => (
                  <Chip key={s} label={s} />
                ))}
              </Box>
            )}

            <TagEditor itemId={itemId!} initialTags={item.tags || []} />

            {item.source_url && (
              <Box mt={2}>
                <Button
                  variant="outlined"
                  size="small"
                  href={item.source_url}
                  target="_blank"
                  rel="noopener"
                >
                  View on Source
                </Button>
              </Box>
            )}
          </>
        )}
      </Box>
    </Drawer>
  );
};

export default DetailDrawer;
