import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ExplorerPage from "./pages/ExplorerPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/explorer" replace />} />
        <Route path="/explorer" element={<ExplorerPage />} />
      </Routes>
    </BrowserRouter>
  );
}
