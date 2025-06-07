# python_ireland_talk_database

A modern “intelligence platform” for Python Ireland—aggregating all past talk and event metadata into a searchable, taggable, and analyzable system.

---

## 🎯 Vision & Phases

We’re building the first part in three iterative phases, with room to grow into a fuller information portal:

### Phase A: Talk Content Explorer

- **Goal:** Ingest Meetup & Sessionize data into Elasticsearch + Postgres, and build a React/Vite front‑end “Explorer”:
  - Filter by date, platform, full‑text search of titles & descriptions
  - Inline tagging of individual items
  - Detail drawer for full metadata (speakers, links, etc.)

### Phase B: Taxonomy Manager

- **Goal:** Curate the raw tags into a structured hierarchy:
  - Tag list with parent/child relationships
  - Drag‑and‑drop tree builder
  - Tag metadata (colors, descriptions, aliases)
  - Saved tag sets for quick filtering

### Phase C: Analytics Dashboard

- **Goal:** Slice & dice tagged content with charts and exports:
  - Tag distribution bar charts
  - Trends over time (multi‑line charts)
  - Co‑occurrence heatmaps
  - CSV/JSON export and alerts on tag‑volume changes

_Long‑term_, incorporate video data, extend this or add apps to integrate member/sponsor/speaker data (CRM) data, build a Q&A interface (with LLMs), and eventually package this as a drop‑in portal for other Python communities. Also could build a data lake to take full ownership of content, fly to the moon, etc.

---

## 🛠 Technology Stack

### Backend (Under Construction)

- **Framework:** FastAPI
- **Primary Store:** PostgreSQL (JSONB)
- **Search & Analytics:** Elasticsearch
- **ORM & Migrations:** SQLAlchemy + Alembic
- **Auth:** OAuth2 / JWT

### Frontend

- **Build Tool:** Vite v6.3.5
- **Library:** React v19.1.0 + TypeScript v5.8.3
- **UI Components:** MUI v7.1.1 (`@mui/material`, `@mui/lab`, `@mui/icons-material`)
- **Data Grid & Pickers:** `@mui/x-data-grid` v8.5.1, `@mui/x-date-pickers` v8.5.1
- **Styling:** Emotion v11.14.0
- **Charts:** Recharts v2.15.3
- **Routing:** React Router v7.6.2
- **Elasticsearch Client:** `@elastic/elasticsearch` (latest)
- **Dates:** date-fns v4.1.0

---

## 📦 Frontend: Install & Run

1. **Ensure Node 20+**:

   ```bash
   node --version   # should be 20.x

   ```

2. **Install dependencies**:

   ```bash
   cd frontend
   npm install
   ```

3. **Configure backend URL** (optional, defaults to http://localhost:8000):
   Create a .env:
   `bash
echo "VITE_BACKEND_URL=http://localhost:8000" > .env
`
4. **Run the development server**:
   ```bash
   npm run dev
   ```
   Open http://localhost:5173/explorer to see the skeleton Explorer page.

## 🚧 Backend: Under Construction

We’ll soon add:

API endpoints in FastAPI for /explorer, /tags, /explorer/{id}, etc.

Ingestion jobs to pull Meetup.com and Sessionize data into Postgres + Elasticsearch.

# Architecture

```mermaid
flowchart LR
  A["Ingest jobs<br/>(Meetup, Sessionize)"]
  B["Data lake<br/>(Postgres, ES)"]
  C["API layer<br/>(FastAPI REST/GraphQL)"]
  D["Frontend<br/>(React + Vite)"]

  A --> B --> C --> D

  %% future work
  subgraph Future
    direction LR
    E["Embeddings<br/>Vector DB (Pinecone or ES)"]
    F["Q&A Service"]
    E --> F
  end

  %% link present to future
  B --> E


```

### LLM Integration (Future)

- **Goal:** Use LLMs to answer questions about the data, generate summaries, and provide insights.
