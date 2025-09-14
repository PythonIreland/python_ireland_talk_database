// frontend/src/components/EnhancedTagEditor.tsx
import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  TextField,
  Alert,
} from "@mui/material";
import { Add as AddIcon, Delete as DeleteIcon } from "@mui/icons-material";
import { useTaxonomy } from "../contexts/TaxonomyContext";
import { TaxonomyAPI } from "../services/taxonomyApi";
import type { TalkTags, TaxonomyValue, Taxonomy } from "../types/taxonomy";

interface EnhancedTagEditorProps {
  talkId: string;
  onTagsUpdated?: () => void;
  readOnly?: boolean;
}

const EnhancedTagEditor: React.FC<EnhancedTagEditorProps> = ({
  talkId,
  onTagsUpdated,
  readOnly = false,
}) => {
  const { taxonomies, getTaxonomyByName } = useTaxonomy();
  const [talkTags, setTalkTags] = useState<TalkTags | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addTagDialogOpen, setAddTagDialogOpen] = useState(false);
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<Taxonomy | null>(
    null
  );
  const [selectedValues, setSelectedValues] = useState<TaxonomyValue[]>([]);

  const loadTalkTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const tags = await TaxonomyAPI.getTalkTags(talkId);
      setTalkTags(tags);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load talk tags");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTalkTags();
  }, [talkId]);

  const handleAddTags = async () => {
    if (!selectedValues.length) return;

    try {
      setError(null);
      await TaxonomyAPI.addTagsToTalk(talkId, {
        taxonomy_value_ids: selectedValues.map((v) => v.id),
      });

      await loadTalkTags();
      setAddTagDialogOpen(false);
      setSelectedTaxonomy(null);
      setSelectedValues([]);
      onTagsUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add tags");
    }
  };

  const handleRemoveTag = async (taxonomyName: string, tagValue: string) => {
    try {
      setError(null);
      const taxonomy = getTaxonomyByName(taxonomyName);
      if (!taxonomy) return;

      const value = taxonomy.values.find((v) => v.value === tagValue);
      if (!value) return;

      await TaxonomyAPI.removeTagFromTalk(talkId, value.id);
      await loadTalkTags();
      onTagsUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove tag");
    }
  };

  const openAddTagDialog = (taxonomy: Taxonomy) => {
    setSelectedTaxonomy(taxonomy);
    setSelectedValues([]);
    setAddTagDialogOpen(true);
  };

  const renderTaxonomySection = (taxonomyName: string, tagValues: string[]) => {
    const taxonomy = getTaxonomyByName(taxonomyName);
    if (!taxonomy) return null;

    return (
      <Card key={taxonomyName} sx={{ mb: 2 }}>
        <CardContent>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={2}
          >
            <Typography variant="h6" component="h3">
              {taxonomy.name}
            </Typography>
            {!readOnly && (
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => openAddTagDialog(taxonomy)}
              >
                Add Tags
              </Button>
            )}
          </Box>

          {taxonomy.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {taxonomy.description}
            </Typography>
          )}

          {tagValues.length === 0 ? (
            <Typography color="text.secondary" sx={{ fontStyle: "italic" }}>
              No tags assigned
            </Typography>
          ) : (
            <Box display="flex" flexWrap="wrap" gap={1}>
              {tagValues.map((tagValue) => {
                const value = taxonomy.values.find((v) => v.value === tagValue);
                return (
                  <Chip
                    key={tagValue}
                    label={tagValue}
                    sx={{
                      backgroundColor: value?.color || "#1976d2",
                      color: "white",
                      "& .MuiChip-deleteIcon": {
                        color: "white",
                      },
                    }}
                    onDelete={
                      !readOnly
                        ? () => handleRemoveTag(taxonomyName, tagValue)
                        : undefined
                    }
                    deleteIcon={<DeleteIcon />}
                  />
                );
              })}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <Typography>Loading tags...</Typography>
      </Box>
    );
  }

  if (!talkTags) {
    return <Alert severity="error">Failed to load talk tags</Alert>;
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h5" component="h2" gutterBottom>
        Talk Tags
      </Typography>

      {/* Auto Tags Section */}
      {talkTags.auto_tags && talkTags.auto_tags.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" component="h3" gutterBottom>
              Auto-Generated Tags
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {talkTags.auto_tags.map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ color: "text.secondary" }}
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Manual Tags by Taxonomy */}
      <Typography variant="h6" component="h3" gutterBottom>
        Manual Tags
      </Typography>

      {Object.keys(talkTags.manual_tags).length === 0 ? (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography color="text.secondary" sx={{ fontStyle: "italic" }}>
              No manual tags assigned
            </Typography>
            {!readOnly && taxonomies.length > 0 && (
              <Button
                startIcon={<AddIcon />}
                onClick={() => openAddTagDialog(taxonomies[0])}
                sx={{ mt: 2 }}
              >
                Add First Tag
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        Object.entries(talkTags.manual_tags).map(([taxonomyName, tagValues]) =>
          renderTaxonomySection(taxonomyName, tagValues)
        )
      )}

      {/* Available Taxonomies (for adding new tag categories) */}
      {!readOnly && taxonomies.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" component="h3" gutterBottom>
              Available Taxonomies
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {taxonomies
                .filter((taxonomy) => !talkTags.manual_tags[taxonomy.name])
                .map((taxonomy) => (
                  <Button
                    key={taxonomy.id}
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => openAddTagDialog(taxonomy)}
                  >
                    Add {taxonomy.name} tags
                  </Button>
                ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Add Tags Dialog */}
      <Dialog
        open={addTagDialogOpen}
        onClose={() => setAddTagDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add Tags to {selectedTaxonomy?.name}</DialogTitle>
        <DialogContent>
          {selectedTaxonomy && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selectedTaxonomy.description}
              </Typography>

              <Autocomplete
                multiple
                options={selectedTaxonomy.values}
                getOptionLabel={(option) => option.value}
                value={selectedValues}
                onChange={(_, newValues) => setSelectedValues(newValues)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Select tags"
                    placeholder="Choose tags..."
                  />
                )}
                renderTags={(tagValue, getTagProps) =>
                  tagValue.map((option, index) => (
                    <Chip
                      {...getTagProps({ index })}
                      key={option.id}
                      label={option.value}
                      sx={{
                        backgroundColor: option.color,
                        color: "white",
                        "& .MuiChip-deleteIcon": {
                          color: "white",
                        },
                      }}
                    />
                  ))
                }
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Chip
                      label={option.value}
                      size="small"
                      sx={{
                        backgroundColor: option.color,
                        color: "white",
                        mr: 1,
                      }}
                    />
                    {option.description && (
                      <Typography variant="body2" color="text.secondary">
                        {option.description}
                      </Typography>
                    )}
                  </Box>
                )}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddTagDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleAddTags}
            variant="contained"
            disabled={selectedValues.length === 0}
          >
            Add {selectedValues.length} Tag
            {selectedValues.length !== 1 ? "s" : ""}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EnhancedTagEditor;
