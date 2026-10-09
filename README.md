# Quantum DNA Sequence Analyzer

> Classical bioinformatics meets **Qiskit Grover's Search Algorithm** for mutation-position and genomic motif discovery.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Quantum | Qiskit 1.3, Qiskit Aer 0.15 |
| Bioinformatics | BioPython |
| Frontend | React 19, Vite 8, TypeScript 6, Tailwind CSS |
| Charts | Recharts |
| Testing (BE) | Pytest + pytest-asyncio + httpx |
| Testing (FE) | Vitest + Testing Library |

---

## Project Structure

```
quantum last/
├── backend/
│   ├── .venv/                      <- Python virtual environment (git-ignored)
│   ├── app/
│   │   ├── api/
│   │   │   └── health.py           <- GET /api/health router
│   │   ├── core/
│   │   │   └── config.py           <- Pydantic-settings configuration
│   │   ├── schemas/
│   │   │   └── health.py           <- Response/request Pydantic models
│   │   ├── services/
│   │   │   ├── dna_processing.py   <- Classical DNA utilities (no Qiskit)
│   │   │   └── quantum_search.py   <- Grover's algorithm (Qiskit only)
│   │   └── main.py                 <- FastAPI app factory + CORS
│   ├── datasets/
│   │   └── sample_brca1.fasta      <- Sample FASTA for development
│   ├── tests/
│   │   ├── test_health.py
│   │   └── test_dna_processing.py
│   ├── pyproject.toml              <- Pytest configuration
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.ts           <- Typed fetch wrapper
│   │   ├── components/
│   │   │   ├── HealthCard.tsx
│   │   │   └── HealthCard.css
│   │   ├── test/
│   │   │   ├── setup.ts
│   │   │   └── HealthCard.test.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css               <- Global design system
│   ├── vite.config.ts
│   └── package.json
├── .gitignore
└── README.md
```

---

## Setup and Run (Windows PowerShell)

### 1. Open the project directory

```powershell
cd "C:\Users\Welcome\OneDrive\Desktop\quantum last"
```

### 2. Backend

```powershell
# Enter backend directory
cd backend

# Create virtual environment (first time only)
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# (Optional) configure environment variables
Copy-Item .env.example .env

# Start the FastAPI development server on port 8000
uvicorn app.main:app --reload --port 8000
```

> Interactive API docs: **http://localhost:8000/docs**

### 3. Frontend

Open a **second** PowerShell tab/window:

```powershell
cd "C:\Users\Welcome\OneDrive\Desktop\quantum last\frontend"

# Install Node dependencies (first time only)
npm install

# Start the Vite dev server on port 5173
npm run dev
```

> App: **http://localhost:5173**

---

## Running Tests

### Backend (Pytest)

```powershell
cd "C:\Users\Welcome\OneDrive\Desktop\quantum last\backend"
.\.venv\Scripts\Activate.ps1
pytest -v
```

Expected output: **19 passed**

### Frontend (Vitest)

```powershell
cd "C:\Users\Welcome\OneDrive\Desktop\quantum last\frontend"
npm test              # single run
npm run test:watch    # watch mode (re-runs on file change)
npm run test:ui       # browser UI for interactive test inspection
```

---

## Architecture Decisions

| Decision | Rationale |
|---|---|
| `dna_processing.py` has zero Qiskit imports | Classical and quantum logic are independently testable |
| Grover probabilities from `AerSimulator` | No hardcoded success rates; all outputs are real simulation counts |
| Vite proxy `/api -> :8000` | Eliminates CORS friction during dev; FastAPI CORS still set for production |
| Pydantic-settings for config | Env vars override defaults; `.env` is never committed |
| App factory pattern in `main.py` | Enables testing without import-time side-effects |

---

## API Reference

### `GET /api/health`

Returns service liveness.

**Response `200 OK`**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "message": "Quantum DNA Sequence Analyzer backend is running."
}
```

---

## Roadmap

- [ ] `POST /api/dna/analyze` - GC content, base counts, validation
- [ ] `POST /api/dna/mutations` - find substitutions between two sequences
- [ ] `POST /api/dna/motif` - classical motif search
- [ ] `POST /api/quantum/grover` - run Grover's algorithm, return circuit and measurement counts
- [ ] Frontend: DNA input panel and results dashboard
- [ ] Frontend: Recharts histogram of Grover measurement distribution
- [ ] Frontend: Quantum circuit SVG viewer
