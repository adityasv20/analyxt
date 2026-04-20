# Analyzt

AI-powered data analyst. Upload a CSV, ask a question, get a full statistical analysis with charts, AI summary, and a conversational data copilot.

```
analyzt/
├── backend/
│   ├── app/
│   │   ├── agent.py          ← Gemini: planning + summary + chat
│   │   ├── main.py           ← FastAPI routes
│   │   ├── models/schemas.py ← Pydantic models
│   │   └── tools/
│   │       ├── analysis.py   ← All statistical tools
│   │       ├── charts.py     ← Matplotlib chart generation
│   │       ├── chat_engine.py← Pandas-first Q&A
│   │       ├── profiling.py  ← Dataset metadata
│   │       ├── reporting.py  ← Markdown report builder
│   │       └── emailer.py    ← SMTP email sender
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx
        ├── index.css
        └── components/
            ├── UploadZone.jsx
            ├── PromptBox.jsx
            ├── LoadingScreen.jsx
            ├── OverviewCards.jsx
            ├── AISummary.jsx
            ├── FindingsTable.jsx
            ├── ChartGallery.jsx
            ├── ChatPanel.jsx
            └── EmailForm.jsx
```

## Setup

### 1. Get a free Gemini API key
Go to **https://aistudio.google.com/app/apikey** → Create API key → Create in **new project**

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate          # Windows

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Open .env and paste your GEMINI_API_KEY

# Run
uvicorn app.main:app --reload --port 8000
```

Check it's working: http://localhost:8000/health → `{"status":"ok","version":"2.0.0"}`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

1. Drop a CSV on the upload zone
2. Type a prompt (or click a suggestion)
3. Click **Run Analysis** (or Cmd+Enter)
4. View the dashboard — AI summary, findings, charts
5. Ask follow-up questions in the **Data Copilot** panel on the right

## Restart after closing

```bash
# Terminal 1 — backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

## Email feature (optional)

In `backend/.env`:
```
SMTP_USER=you@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx   # 16-char Gmail App Password
```
Get an App Password: https://myaccount.google.com/apppasswords (requires 2FA enabled)

## Tech stack

| Layer    | Tech                                      |
|----------|-------------------------------------------|
| Frontend | React 18, Vite, Tailwind CSS              |
| Backend  | Python FastAPI, uvicorn                   |
| Analysis | pandas, numpy, matplotlib, seaborn, scipy |
| AI       | Google Gemini (free tier)                 |
| Fonts    | Instrument Serif, Geist, Geist Mono       |
