// src/pages/ExplorerPage.tsx
import React, { useState, useEffect } from "react";
import { Container, Box, Paper, IconButton, TextField } from "@mui/material";
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
import { fetchExplorerItems } from "../utils/api";
import type { ExplorerItem } from "../utils/api";

const columns: GridColDef[] = [
  { field: "date", headerName: "Date", width: 120 },
  { field: "platform", headerName: "Platform", width: 120 },
  { field: "title", headerName: "Title", width: 300 },
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
  const [fromDate, setFromDate] = useState<Date | null>(null);
  const [toDate, setToDate] = useState<Date | null>(null);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // pagination state for DataGrid v6
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 50,
  });

  useEffect(() => {
    setLoading(true);
    fetchExplorerItems({ from: fromDate, to: toDate, search })
      .then((data) => setItems(data))
      .finally(() => setLoading(false));
  }, [fromDate, toDate, search]);

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      {/* Filter bar */}
      <Paper sx={{ p: 2, mb: 2 }} elevation={1}>
        <Box display="flex" alignItems="center" flexWrap="wrap" gap={1}>
          <DatePicker
            label="From"
            value={fromDate}
            onChange={setFromDate}
            slotProps={{
              textField: { sx: { mr: 2 }, size: "small" },
            }}
          />
          <DatePicker
            label="To"
            value={toDate}
            onChange={setToDate}
            slotProps={{
              textField: { sx: { mr: 2 }, size: "small" },
            }}
          />
          <TextField
            label="Search"
            variant="outlined"
            size="small"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ width: 300, mr: 1 }}
          />
          <IconButton>
            <FilterListIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Data grid with controlled pagination */}
      <Box sx={{ height: "calc(100vh - 200px)", width: "100%" }}>
        <DataGrid
          rows={items}
          columns={columns}
          loading={loading}
          pagination
          paginationModel={paginationModel}
          onPaginationModelChange={(model) => setPaginationModel(model)}
          pageSizeOptions={[50]}
          onRowClick={(params) => setSelectedId(params.id as string)}
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
