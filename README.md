# HireLens AI — Monorepo

Welcome to the **HireLens AI** monorepo. HireLens is an AI-powered Career Copilot that guides job seekers from resume optimization through interview preparation and application tracking.

## Repository Structure

```
HireLens-AI/
├── docs/                               # Product and architecture documentation
│   ├── PRD.md                          # Startup-grade Product Requirements Document
│
├── backend/                            # FastAPI Application
│   ├── app/
│   │   ├── main.py                     # Entry point
│   │   ├── config.py                   # Pydantic Settings
│   │   ├── db/                         # Database connections & session makers
│   │   ├── models/                     # SQLAlchemy 2.0 ORM Models
│   │   └── ...
│   ├── alembic/                        # Migration scripts
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                           # Next.js Application
│   ├── src/
│   │   └── app/                        # App Router Pages
│   ├── package.json
│   └── ...
│
└── docker-compose.yml                  # Local orchestration (DB, Redis, MinIO, API)
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- [Python 3.11+](https://www.python.org/) (for running backend locally)
- [Node.js 20+](https://nodejs.org/) (for running frontend locally)

---

### Run using Docker Compose (Recommended)

1. Start all services:
   ```bash
   docker compose up --build
   ```

2. Run the database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

3. The services will be accessible at:
   - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   - **Frontend App:** [http://localhost:3000](http://localhost:3000)
   - **MinIO Console:** [http://localhost:9001](http://localhost:9001) (Credentials: `minioadmin` / `minioadmin`)

---

### Run Locally (Without Docker)

#### 1. Start External Services
Ensure you have local instances of PostgreSQL, Redis, and MinIO running, and update `backend/.env` with their connections.

#### 2. Backend Setup
1. Change directory to backend:
   ```bash
   cd backend
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Start backend development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 3. Frontend Setup
1. Change directory to frontend:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start frontend dev server:
   ```bash
   npm run dev
   ```
4. Access the web app at [http://localhost:3000](http://localhost:3000).

---

## Continuous Integration & Deployment

GitHub Actions workflow configurations can be found in `.github/workflows/`.
- `ci.yml`: Performs linting (Ruff/ESlint) and build checks.
- `deploy.yml`: Prepared deploy commands for staging/production.
