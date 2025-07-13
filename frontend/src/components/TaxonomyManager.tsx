// frontend/src/components/TaxonomyManager.tsx
import React, { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Label as LabelIcon,
} from "@mui/icons-material";
import { useTaxonomy } from "../contexts/TaxonomyContext";
import type { Taxonomy, TaxonomyValue } from "../types/taxonomy";

interface TaxonomyManagerProps {
  readOnly?: boolean;
}

const TaxonomyManager: React.FC<TaxonomyManagerProps> = ({
  readOnly = false,
}) => {
  const {
    loading,
    error,
    createTaxonomy,
    updateTaxonomy,
    deleteTaxonomy,
    createTaxonomyValue,
    updateTaxonomyValue,
    deleteTaxonomyValue,
    getSystemTaxonomies,
    getUserTaxonomies,
  } = useTaxonomy();

  const [createTaxonomyOpen, setCreateTaxonomyOpen] = useState(false);
  const [editTaxonomyOpen, setEditTaxonomyOpen] = useState(false);
  const [createValueOpen, setCreateValueOpen] = useState(false);
  const [editValueOpen, setEditValueOpen] = useState(false);
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<Taxonomy | null>(
    null
  );
  const [selectedValue, setSelectedValue] = useState<TaxonomyValue | null>(
    null
  );
  const [newTaxonomyName, setNewTaxonomyName] = useState("");
  const [newTaxonomyDescription, setNewTaxonomyDescription] = useState("");
  const [newValueName, setNewValueName] = useState("");
  const [newValueDescription, setNewValueDescription] = useState("");
  const [newValueColor, setNewValueColor] = useState("#1976d2");

  const systemTaxonomies = getSystemTaxonomies();
  const userTaxonomies = getUserTaxonomies();

  const handleCreateTaxonomy = async () => {
    if (!newTaxonomyName.trim()) return;

    try {
      await createTaxonomy(
        newTaxonomyName.trim(),
        newTaxonomyDescription.trim() || undefined
      );
      setCreateTaxonomyOpen(false);
      setNewTaxonomyName("");
      setNewTaxonomyDescription("");
    } catch (error) {
      console.error("Failed to create taxonomy:", error);
    }
  };

  const handleEditTaxonomy = async () => {
    if (!selectedTaxonomy || !newTaxonomyName.trim()) return;

    try {
      await updateTaxonomy(
        selectedTaxonomy.id,
        newTaxonomyName.trim(),
        newTaxonomyDescription.trim() || undefined
      );
      setEditTaxonomyOpen(false);
      setSelectedTaxonomy(null);
      setNewTaxonomyName("");
      setNewTaxonomyDescription("");
    } catch (error) {
      console.error("Failed to update taxonomy:", error);
    }
  };

  const handleDeleteTaxonomy = async (taxonomy: Taxonomy) => {
    if (
      !window.confirm(
        `Delete taxonomy "${taxonomy.name}"? This will also delete all its values.`
      )
    )
      return;

    try {
      await deleteTaxonomy(taxonomy.id);
    } catch (error) {
      console.error("Failed to delete taxonomy:", error);
    }
  };

  const handleCreateValue = async () => {
    if (!selectedTaxonomy || !newValueName.trim()) return;

    try {
      await createTaxonomyValue(
        selectedTaxonomy.id,
        newValueName.trim(),
        newValueDescription.trim() || undefined,
        newValueColor
      );
      setCreateValueOpen(false);
      setNewValueName("");
      setNewValueDescription("");
      setNewValueColor("#1976d2");
    } catch (error) {
      console.error("Failed to create taxonomy value:", error);
    }
  };

  const handleEditValue = async () => {
    if (!selectedValue || !newValueName.trim()) return;

    try {
      await updateTaxonomyValue(selectedValue.id, {
        value: newValueName.trim(),
        description: newValueDescription.trim() || undefined,
        color: newValueColor,
      });
      setEditValueOpen(false);
      setSelectedValue(null);
      setNewValueName("");
      setNewValueDescription("");
      setNewValueColor("#1976d2");
    } catch (error) {
      console.error("Failed to update taxonomy value:", error);
    }
  };

  const handleDeleteValue = async (value: TaxonomyValue) => {
    if (!window.confirm(`Delete value "${value.value}"?`)) return;

    try {
      await deleteTaxonomyValue(value.id);
    } catch (error) {
      console.error("Failed to delete taxonomy value:", error);
    }
  };

  const openEditTaxonomy = (taxonomy: Taxonomy) => {
    setSelectedTaxonomy(taxonomy);
    setNewTaxonomyName(taxonomy.name);
    setNewTaxonomyDescription(taxonomy.description);
    setEditTaxonomyOpen(true);
  };

  const openCreateValue = (taxonomy: Taxonomy) => {
    setSelectedTaxonomy(taxonomy);
    setCreateValueOpen(true);
  };

  const openEditValue = (value: TaxonomyValue) => {
    setSelectedValue(value);
    setNewValueName(value.value);
    setNewValueDescription(value.description);
    setNewValueColor(value.color);
    setEditValueOpen(true);
  };

  const renderTaxonomyGroup = (
    title: string,
    taxonomiesList: Taxonomy[],
    canEdit: boolean
  ) => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography variant="h6" component="h2">
            {title}
          </Typography>
          {canEdit && !readOnly && (
            <Button
              startIcon={<AddIcon />}
              variant="outlined"
              size="small"
              onClick={() => setCreateTaxonomyOpen(true)}
            >
              Add Taxonomy
            </Button>
          )}
        </Box>

        {taxonomiesList.length === 0 ? (
          <Typography color="text.secondary">No taxonomies found</Typography>
        ) : (
          taxonomiesList.map((taxonomy) => (
            <Accordion key={taxonomy.id} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" width="100%">
                  <LabelIcon sx={{ mr: 1, color: "primary.main" }} />
                  <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                    {taxonomy.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mr: 2 }}
                  >
                    {taxonomy.values.length} values
                  </Typography>
                  {!readOnly && canEdit && (
                    <Box onClick={(e) => e.stopPropagation()}>
                      <IconButton
                        size="small"
                        onClick={() => openEditTaxonomy(taxonomy)}
                        sx={{ mr: 1 }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteTaxonomy(taxonomy)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  {taxonomy.description}
                </Typography>

                <Box
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  mb={2}
                >
                  <Typography variant="subtitle2">Values</Typography>
                  {!readOnly && (
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => openCreateValue(taxonomy)}
                    >
                      Add Value
                    </Button>
                  )}
                </Box>

                <Box display="flex" flexWrap="wrap" gap={1}>
                  {taxonomy.values.map((value) => (
                    <Chip
                      key={value.id}
                      label={value.value}
                      sx={{
                        backgroundColor: value.color,
                        color: "white",
                        "& .MuiChip-deleteIcon": {
                          color: "white",
                        },
                      }}
                      onDelete={
                        !readOnly ? () => openEditValue(value) : undefined
                      }
                      deleteIcon={<EditIcon />}
                    />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <Typography>Loading taxonomies...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {renderTaxonomyGroup("System Taxonomies", systemTaxonomies, false)}
      {renderTaxonomyGroup("Custom Taxonomies", userTaxonomies, true)}

      {/* Create Taxonomy Dialog */}
      <Dialog
        open={createTaxonomyOpen}
        onClose={() => setCreateTaxonomyOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Taxonomy</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Taxonomy Name"
            fullWidth
            variant="outlined"
            value={newTaxonomyName}
            onChange={(e) => setNewTaxonomyName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newTaxonomyDescription}
            onChange={(e) => setNewTaxonomyDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTaxonomyOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTaxonomy} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Taxonomy Dialog */}
      <Dialog
        open={editTaxonomyOpen}
        onClose={() => setEditTaxonomyOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Taxonomy</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Taxonomy Name"
            fullWidth
            variant="outlined"
            value={newTaxonomyName}
            onChange={(e) => setNewTaxonomyName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newTaxonomyDescription}
            onChange={(e) => setNewTaxonomyDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTaxonomyOpen(false)}>Cancel</Button>
          <Button onClick={handleEditTaxonomy} variant="contained">
            Update
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Value Dialog */}
      <Dialog
        open={createValueOpen}
        onClose={() => setCreateValueOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Value to {selectedTaxonomy?.name}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Value Name"
            fullWidth
            variant="outlined"
            value={newValueName}
            onChange={(e) => setNewValueName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={newValueDescription}
            onChange={(e) => setNewValueDescription(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Box display="flex" alignItems="center" gap={2}>
            <TextField
              label="Color"
              type="color"
              value={newValueColor}
              onChange={(e) => setNewValueColor(e.target.value)}
              sx={{ width: 100 }}
            />
            <Chip
              label={newValueName || "Preview"}
              sx={{
                backgroundColor: newValueColor,
                color: "white",
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateValueOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateValue} variant="contained">
            Add Value
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Value Dialog */}
      <Dialog
        open={editValueOpen}
        onClose={() => setEditValueOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Value</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Value Name"
            fullWidth
            variant="outlined"
            value={newValueName}
            onChange={(e) => setNewValueName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={newValueDescription}
            onChange={(e) => setNewValueDescription(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <TextField
              label="Color"
              type="color"
              value={newValueColor}
              onChange={(e) => setNewValueColor(e.target.value)}
              sx={{ width: 100 }}
            />
            <Chip
              label={newValueName || "Preview"}
              sx={{
                backgroundColor: newValueColor,
                color: "white",
              }}
            />
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Button
              color="error"
              onClick={() => {
                if (selectedValue) handleDeleteValue(selectedValue);
                setEditValueOpen(false);
              }}
            >
              Delete Value
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditValueOpen(false)}>Cancel</Button>
          <Button onClick={handleEditValue} variant="contained">
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaxonomyManager;
