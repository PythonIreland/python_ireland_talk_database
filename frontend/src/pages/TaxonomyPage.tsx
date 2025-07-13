// frontend/src/pages/TaxonomyPage.tsx
import React, { useState } from "react";
import {
  Container,
  Box,
  Typography,
  Tab,
  Tabs,
  Paper,
  Button,
  Alert,
} from "@mui/material";
import {
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  PlayArrow as InitializeIcon,
} from "@mui/icons-material";
import { TaxonomyProvider } from "../contexts/TaxonomyContext";
import TaxonomyManager from "../components/TaxonomyManager";
import { TaxonomyAPI } from "../services/taxonomyApi";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`taxonomy-tabpanel-${index}`}
      aria-labelledby={`taxonomy-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TaxonomyPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [initializingDefaults, setInitializingDefaults] = useState(false);
  const [initializeMessage, setInitializeMessage] = useState<string | null>(
    null
  );

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleInitializeDefaults = async () => {
    try {
      setInitializingDefaults(true);
      setInitializeMessage(null);
      await TaxonomyAPI.initializeDefaultTaxonomies();
      setInitializeMessage("Default taxonomies initialized successfully!");
      // Refresh the page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      setInitializeMessage(
        `Failed to initialize defaults: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setInitializingDefaults(false);
    }
  };

  return (
    <TaxonomyProvider>
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            Taxonomy Management
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" paragraph>
            Manage taxonomies and organize your talk database with structured
            tagging
          </Typography>

          {initializeMessage && (
            <Alert
              severity={
                initializeMessage.includes("Failed") ? "error" : "success"
              }
              sx={{ mb: 3 }}
            >
              {initializeMessage}
            </Alert>
          )}

          <Paper sx={{ mt: 3 }}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                aria-label="taxonomy management tabs"
              >
                <Tab
                  icon={<SettingsIcon />}
                  label="Manage Taxonomies"
                  id="taxonomy-tab-0"
                  aria-controls="taxonomy-tabpanel-0"
                />
                <Tab
                  icon={<AnalyticsIcon />}
                  label="Analytics"
                  id="taxonomy-tab-1"
                  aria-controls="taxonomy-tabpanel-1"
                  disabled
                />
                <Tab
                  icon={<InitializeIcon />}
                  label="Initialize"
                  id="taxonomy-tab-2"
                  aria-controls="taxonomy-tabpanel-2"
                />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <TaxonomyManager />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Box textAlign="center" py={4}>
                <Typography variant="h6" color="text.secondary">
                  Analytics Dashboard
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Coming soon - taxonomy usage analytics and insights
                </Typography>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Box textAlign="center" py={4}>
                <Typography variant="h6" gutterBottom>
                  Initialize Default Taxonomies
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Set up the standard taxonomy structure including difficulty
                  levels, topics, and conference types. This will create system
                  taxonomies that provide a consistent foundation for organizing
                  talks.
                </Typography>
                <Button
                  variant="contained"
                  onClick={handleInitializeDefaults}
                  disabled={initializingDefaults}
                  size="large"
                >
                  {initializingDefaults
                    ? "Initializing..."
                    : "Initialize Default Taxonomies"}
                </Button>
              </Box>
            </TabPanel>
          </Paper>
        </Box>
      </Container>
    </TaxonomyProvider>
  );
};

export default TaxonomyPage;
