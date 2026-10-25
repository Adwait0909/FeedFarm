# 🐄 Maharashtra Veterinary & Animal Welfare Assistance

Standalone web app — ready to deploy, and designed to integrate with your existing Smart Farm Management System.

**Data source:** Maharashtra Animal Husbandry Department (DAHD) official KML files  
**Facilities:** ~1,987 Veterinary Dispensaries + 199 District/Taluka Clinics = **2,186 real facilities**

---

## Project Structure

```
vet-app/
├── backend/
│   ├── main.py                          ← FastAPI entry point
│   ├── config.py                        ← Settings (reads .env)
│   ├── database.py                      ← SQLAlchemy async engine
│   ├── requirements.txt
│   ├── .env.example                     ← Copy to .env and fill in
│   ├── data/
│   │   ├── Veterinary_Dispensary.kml
│   │   └── District_and_Taluka_Level_Veterinary_Clinics.kml
│   ├── models/
│   │   ├── veterinary.py                ← SQLAlchemy ORM model
│   │   └── schemas.py                   ← Pydantic request/response schemas
│   ├── routes/
│   │   └── veterinary.py                ← FastAPI route handlers
│   ├── services/
│   │   └── veterinary_service.py        ← Business logic
│   ├── utils/
│   │   ├── kml_parser.py               ← KML file parser
│   │   └── geo.py                      ← Haversine distance
│   ├── migrations/
│   │   └── 001_create_veterinary_facilities.sql
│   └── scripts/
│       └── import_kml.py               ← One-time data import
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── pages/
        │   └── VeterinaryAssistance.jsx
        ├── components/
        │   ├── VeterinaryLocator.jsx    ← Main feature component
        │   ├── FacilityCard.jsx
        │   ├── FacilityDetailModal.jsx
        │   ├── VetMap.jsx               ← Leaflet map
        │   └── DiseaseRiskBanner.jsx   ← Disease module integration
        ├── services/
        │   └── veterinaryApi.js
        └── hooks/
            └── useGeolocation.js
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+

---

### Step 1 — PostgreSQL Database

```sql
CREATE DATABASE vet_assist;
```

Or use your existing database — the table is added without touching anything else.

---

### Step 2 — Backend Setup

```bash
cd backend

# Copy and configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your PostgreSQL connection string

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the next commands from the integrations/vet-app folder (parent of backend/)
# Import KML data into database (run ONCE)
python -m backend.scripts.import_kml

# Start the API server
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### Step 3 — Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

### Step 4 — Verify It Works

Test the nearby search endpoint:
```
GET http://localhost:8000/api/veterinary/nearby?latitude=19.0760&longitude=72.8777&radius=25&limit=10
```

Test district search:
```
GET http://localhost:8000/api/veterinary/search/district?district=Pune
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/veterinary/import` | Import KML files into DB |
| `GET`  | `/api/veterinary/nearby` | Nearest facilities by GPS |
| `GET`  | `/api/veterinary/search/district` | Search by district/taluka |
| `GET`  | `/api/veterinary/districts` | All districts (for dropdown) |
| `GET`  | `/api/veterinary/talukas?district=X` | Talukas for a district |
| `GET`  | `/api/veterinary/stats` | Facility counts |
| `GET`  | `/api/veterinary/{id}` | Single facility details |

### Nearby Search Parameters
```
/api/veterinary/nearby
  ?latitude=19.0760
  &longitude=72.8777
  &radius=25          (km, default 25, max 200)
  &limit=10           (default 10, max 100)
  &facility_type=Veterinary+Dispensary   (optional filter)
```

---

## Integrating with Your Existing System

### Option A — Add routes to existing FastAPI app

In your existing `main.py`:
```python
from routes.veterinary import router as vet_router
app.include_router(vet_router)
```

Copy `models/`, `routes/`, `services/`, `utils/` into your project.

### Option B — Add React component to existing frontend

Import the component anywhere in your existing React app:
```jsx
import VeterinaryLocator from './components/VeterinaryLocator'

// Standalone
<VeterinaryLocator />

// With disease risk integration
<VeterinaryLocator riskLevel="high" animalName="Dairy Cow #3" />
```

### Option C — Link from disease module

```jsx
// In your existing livestock/disease component:
import { useNavigate } from 'react-router-dom'

const navigate = useNavigate()

// When risk is high:
<button onClick={() => navigate('/veterinary')}>
  Find Nearby Vet
</button>
```

---

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vet_assist
SYNC_DATABASE_URL=postgresql://user:password@localhost:5432/vet_assist
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
KML_DATA_DIR=./data
```

---

## Re-importing KML Data (when DAHD updates files)

1. Replace the KML files in `backend/data/`
2. Run: `python -m backend.scripts.import_kml`

Duplicate records are automatically skipped. Only new facilities are added.

---

## Deployment Notes

- For production, use `uvicorn backend.main:app --host 0.0.0.0 --port 8000` (behind nginx)
- Frontend: `npm run build` → serve `dist/` folder
- Set `CORS_ORIGINS` in `.env` to your production domain
- The `POST /api/veterinary/import` endpoint should be protected in production (add your auth middleware)
