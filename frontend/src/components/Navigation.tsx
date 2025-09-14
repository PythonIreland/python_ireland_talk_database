// frontend/src/components/Navigation.tsx
import React from "react";
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import {
  Search as SearchIcon,
  Settings as SettingsIcon,
} from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AppBar position="sticky">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Python Ireland Talk Database
        </Typography>

        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            color="inherit"
            startIcon={<SearchIcon />}
            onClick={() => navigate("/explorer")}
            variant={location.pathname === "/explorer" ? "outlined" : "text"}
          >
            Explorer
          </Button>

          <Button
            color="inherit"
            startIcon={<SettingsIcon />}
            onClick={() => navigate("/taxonomy")}
            variant={location.pathname === "/taxonomy" ? "outlined" : "text"}
          >
            Taxonomy
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
