// frontend/src/pages/ExplorerPage.tsx
import React, { useState, useEffect } from "react";
import {
  Container,
  Box,
  Paper,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Alert,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type {
  GridColDef,
  GridRenderCellParams,
  GridPaginationModel,
} from "@mui/x-data-grid";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import FilterListIcon from "@mui/icons-material/FilterList";

import TagEditor from "../components/TagEditor";
import DetailDrawer from "../components/DetailDrawer";
import { fetchExplorerItems, fetchTalkTypes } from "../utils/api";
import type { ExplorerItem } from "../utils/api";

const columns: GridColDef[] = [
  {
    field: "date",
    headerName: "Date",
    width: 120,
    renderCell: (params) => {
      const date = new Date(params.value);
      return date.toLocaleDateString();
    },
  },
  {
    field: "platform",
    headerName: "Platform",
    width: 100,
    renderCell: (params: GridRenderCellParams<string>) => (
      <Chip
        label={params.value?.toUpperCase()}
        size="small"
        color={params.value === "pycon" ? "primary" : "secondary"}
      />
    ),
  },
  { field: "title", headerName: "Title", width: 350, flex: 1 },
  {
    field: "speakers",
    headerName: "Speakers",
    width: 200,
    renderCell: (params: GridRenderCellParams<string[]>) => (
      <Box>
        {params.value?.slice(0, 2).map((speaker, idx) => (
          <Typography key={idx} variant="caption" display="block">
            {speaker}
          </Typography>
        ))}
        {params.value && params.value.length > 2 && (
          <Typography variant="caption" color="textSecondary">
            +{params.value.length - 2} more
          </Typography>
        )}
      </Box>
    ),
  },
  {
    field: "tags",
    headerName: "Tags",
    width: 250,
    renderCell: (params: GridRenderCellParams<string[]>) => (
      <TagEditor itemId={params.row.id} initialTags={params.value || []} />
    ),
  },
];

const ExplorerPage: React.FC = () => {
  const [items, setItems] = useState<ExplorerItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fromDate, setFromDate] = useState<Date | null>(null);
  const [toDate, setToDate] = useState<Date | null>(null);
  const [search, setSearch] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [availablePlatforms, setAvailablePlatforms] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 50,
  });

  // Load available platforms
  useEffect(() => {
    fetchTalkTypes().then(setAvailablePlatforms);
  }, []);

  // Load data when filters change
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchExplorerItems({
          from: fromDate,
          to: toDate,
          search: search || undefined,
          talk_types:
            selectedPlatforms.length > 0 ? selectedPlatforms : undefined,
          limit: 100, // Get more items for better UX
        });
        setItems(data);
      } catch (err) {
        setError("Failed to load talks. Make sure your backend is running.");
        console.error("Error loading data:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [fromDate, toDate, search, selectedPlatforms]);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Typography variant="h4" gutterBottom>
        Python Ireland Talk Explorer
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Filter bar */}
      <Paper sx={{ p: 2, mb: 2 }} elevation={1}>
        <Box display="flex" alignItems="center" flexWrap="wrap" gap={2}>
          <DatePicker
            label="From"
            value={fromDate}
            onChange={setFromDate}
            slotProps={{
              textField: { size: "small", sx: { width: 150 } },
            }}
          />
          <DatePicker
            label="To"
            value={toDate}
            onChange={setToDate}
            slotProps={{
              textField: { size: "small", sx: { width: 150 } },
            }}
          />
          <TextField
            label="Search"
            variant="outlined"
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ width: 300 }}
            placeholder="Search titles, descriptions, speakers..."
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Platforms</InputLabel>
            <Select
              multiple
              value={selectedPlatforms}
              onChange={(e) => setSelectedPlatforms(e.target.value as string[])}
              renderValue={(selected) => (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={value.toUpperCase()}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            >
              {availablePlatforms.map((platform) => (
                <MenuItem key={platform} value={platform}>
                  {platform.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ mt: 1, display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="body2" color="textSecondary">
            {loading ? "Loading..." : `${items.length} talks found`}
          </Typography>
        </Box>
      </Paper>

      {/* Data grid */}
      <Box sx={{ height: "calc(100vh - 280px)", width: "100%" }}>
        <DataGrid
          rows={items}
          columns={columns}
          loading={loading}
          pagination
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[25, 50, 100]}
          onRowClick={(params) => setSelectedId(params.id as string)}
          sx={{
            "& .MuiDataGrid-row:hover": {
              cursor: "pointer",
            },
          }}
        />
      </Box>

      {/* Detail drawer */}
      <DetailDrawer
        open={!!selectedId}
        itemId={selectedId}
        onClose={() => setSelectedId(null)}
      />
    </Container>
  );
};

export default ExplorerPage;
