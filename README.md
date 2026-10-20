# ✈️ TripMind AI — Autonomous Multi-Agent Travel Planner

> An intelligent, production-grade **Multi-Agent Travel Planning System** that coordinates specialized AI agents to generate real-world itineraries with live weather intelligence, dynamic replanning, interactive geospatial maps, and budget guardrails.

---

## 🌟 Key Architecture & Agent Mesh

Rather than relying on a single monolithic prompt, TripMind AI decomposes travel planning into **6 specialized autonomous agents**:

| Agent Name | Role & Responsibility | Output / Actions |
| :--- | :--- | :--- |
| **🤖 Orchestrator Agent** | Coordinates the planning pipeline, dispatches tasks, and logs real-time agent execution traces. | Inter-agent trace stream, aggregated response |
| **🌦️ Weather & Geo Agent** | Resolves destination coordinates and queries real-time meteorological forecasts via Open-Meteo. | Geocoding (`lat`, `lng`), daily temperatures, rain probability & alerts |
| **🔍 Destination Research Agent** | Gathers real points of interest (POIs), operating hours, entrance tickets, and indoor/outdoor venues. | Curated/synthesized POIs with spatial offsets and category tags |
| **🗺️ Itinerary Planning Agent** | Clusters attractions by geography and time of day, optimizing transit vectors and pacing. | Structured morning, afternoon, and evening daily schedule |
| **💰 Budget Optimizer Agent** | Audits planned expenses across 5 categories, detects overruns, and generates 3 comparative tiers. | Backpacker vs Comfort vs Luxury comparison, cost-saving recommendations |
| **🛡️ Critic & Validation Agent** | Performs automated sanity audits on geographic proximity, timing feasibility, and budget adherence. | Feasibility Score (e.g. 98/100), verified vs estimated data counts |

---

## 🚀 Features

- **Multi-Agent Deliberation & Thought Stream**: Real-time transparency log displaying how agents collaborate, deliberate, and pass context.
- **Dual-Engine Execution**:
  - **Google Gemini 2.5 Flash**: Structured JSON generative synthesis when an API key is configured.
  - **Autonomous Heuristic Fallback**: 100% offline-ready heuristic simulation that works immediately without keys or external dependencies.
- **Interactive Geospatial Maps**: Embedded **Leaflet.js + OpenStreetMap** with custom color-coded day markers, interactive attraction popups, and route polylines.
- **Live Environmental & Weather Adaptation**: Automatically evaluates rain risk and high temperatures, recommending indoor alternatives or weather gear.
- **⚡ Surgical Single-Day Replanning**: Re-optimize or regenerate any single day without resetting or losing the rest of your trip plan (`POST /api/replan-day`).
- **3-Tier Budget Optimization**: Side-by-side financial breakdown across *Backpacker*, *Balanced Comfort*, and *Luxury Premium*.
- **PDF Export & Print Ready**: Clean, print-styled stylesheet allowing instant export to PDF travel booklets.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, HTTPX, Uvicorn
- **AI / LLM**: Google Gemini API (`gemini-2.5-flash`), Custom Multi-Agent Orchestration
- **Live APIs**: Open-Meteo API (Free Geocoding & Weather Telemetry)
- **Frontend**: Modern Responsive HTML5, Tailwind CSS, Leaflet.js, OpenStreetMap
- **Persistence & Formatting**: RESTful JSON Schemas, Print CSS for PDF export

---

## 🏁 Quick Start

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/TripMind-AI.git
cd TripMind-AI

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pydantic python-dotenv httpx
```

### 2. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Add your Google Gemini API Key if you want live LLM generation:
```ini
GEMINI_API_KEY=AIzaSy...
```
*(Note: If omitted, the app will run seamlessly in autonomous heuristic simulation mode.)*

### 3. Run Application
```bash
uvicorn app.main:app --reload --port 8000
```
Open your browser at:
👉 **`http://localhost:8000`**

---

## 📡 API Endpoints

- `GET /` — Serves the interactive travel planning dashboard.
- `GET /api/health` — Returns system status, configured AI engine, and active agents.
- `POST /api/plan` — Executes the full multi-agent travel planning pipeline.
- `POST /api/replan-day` — Surgically regenerates an individual day's itinerary.

---

## 🛣️ Roadmap

- [x] **Stage 1**: Core Travel Planner & Working Frontend
- [x] **Stage 2**: Multi-Agent Integration (Orchestrator, Research, Weather, Itinerary, Budget, Critic)
- [x] **Stage 3**: Real-World Information (Leaflet Map, Live Weather via Open-Meteo, Verified POIs)
- [x] **Stage 4**: Intelligent Budget Optimization (3-Tier Comparison & Overrun Detection)
- [x] **Stage 5**: Dynamic Replanning (Single-Day Surgical Regeneration Endpoint)
- [ ] **Stage 6**: Group Travel Intelligence (Collaborative traveler voting & consensus)
- [ ] **Stage 7**: User Accounts & SQLite Trip Persistence

