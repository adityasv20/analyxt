"""
app/main.py — Analyzt FastAPI application.

Routes:
  POST /upload    Upload a CSV
  POST /analyze   Full analysis pipeline
  POST /chat      Dataset Q&A
  POST /email     Email the report
  GET  /outputs/  Serve chart images
  GET  /health    Health check
"""

import os
from typing import List

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.agent import generate_summary, plan_analysis
from app.models.schemas import (
    AnalysisRequest, AnalysisResult, ChatRequest, ChatResponse,
    EmailRequest, FindingItem,
)
from app.tools.analysis import (
    analyze_categorical, analyze_correlations, analyze_duplicates,
    analyze_missing, analyze_outliers, analyze_stats,
)
from app.tools.charts import generate_charts
from app.tools.chat_engine import answer_question
from app.tools.emailer import send_report_email
from app.tools.profiling import profile_dataset
from app.tools.reporting import build_report

# ── Directories ───────────────────────────────────────────────────────────────
for d in ["uploads", "outputs", "outputs/charts"]:
    os.makedirs(d, exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Analyzt", version="2.0.0")

frontend_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
configured_frontend = os.getenv("FRONTEND_URL", "").strip()
if configured_frontend:
    frontend_origins.extend(
        origin.strip()
        for origin in configured_frontend.split(",")
        if origin.strip()
    )
frontend_origins = list(dict.fromkeys(frontend_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# ── Step map ─────────────────────────────────────────────────────────────────
def _run_steps(plan: List[str], df: pd.DataFrame) -> tuple:
    """Execute analysis steps and return (findings, chart_paths)."""
    findings: List[FindingItem] = []
    charts: List[str] = []

    STEP_MAP = {
        "missing_values":      lambda: analyze_missing(df),
        "duplicates_check":    lambda: analyze_duplicates(df),
        "summary_statistics":  lambda: analyze_stats(df),
        "outlier_detection":   lambda: analyze_outliers(df),
        "correlation_analysis":lambda: analyze_correlations(df),
        "categorical_analysis":lambda: analyze_categorical(df),
    }

    for step in plan:
        if step == "generate_charts":
            try:
                charts = generate_charts(df)
            except Exception as e:
                print(f"[main] charts failed: {e}")
        elif step in STEP_MAP:
            try:
                result = STEP_MAP[step]()
                if result:
                    findings.extend(result)
            except Exception as e:
                print(f"[main] step '{step}' failed: {e}")
                findings.append(FindingItem(label=f"Error: {step}", value="Failed", note=str(e)))

    return findings, charts


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted.")
    safe = os.path.basename(file.filename).replace(" ", "_")
    path = os.path.join("uploads", safe)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"filename": safe, "size_bytes": len(content)}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(req: AnalysisRequest):
    path = os.path.join("uploads", req.filename)
    if not os.path.exists(path):
        raise HTTPException(404, f"File not found: {req.filename}")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise HTTPException(400, f"Could not read CSV: {e}")

    if df.empty:
        raise HTTPException(400, "The uploaded file is empty.")

    # Profile
    overview = profile_dataset(df)

    # Plan
    try:
        plan = plan_analysis(req.prompt, overview)
    except Exception as e:
        print(f"[main] planning failed: {e}")
        plan = ["summary_statistics", "missing_values", "generate_charts"]

    # Execute
    findings, charts = _run_steps(plan, df)

    # Summarize
    try:
        summary = generate_summary(req.prompt, overview, findings, len(charts))
    except Exception as e:
        print(f"[main] summary failed: {e}")
        summary = f"⚠ Summary unavailable: {e}"

    # Report
    report_text, report_filename = build_report(
        req.filename, overview, findings, charts, summary
    )

    return AnalysisResult(
        dataset_overview=overview,
        plan=plan,
        findings=findings,
        chart_paths=charts,
        llm_summary=summary,
        report_text=report_text,
        report_filename=report_filename,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.filename:
        raise HTTPException(400, "filename is required")
    if not req.question.strip():
        raise HTTPException(400, "question cannot be empty")
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        answer, method = answer_question(req.filename, req.question.strip(), history)
        return ChatResponse(answer=answer, method=method, question=req.question.strip())
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        print(f"[chat] error: {e}")
        raise HTTPException(500, f"Chat failed: {e}")


@app.post("/email")
async def email(req: EmailRequest):
    result = send_report_email(req.to_email, req.report_filename, req.subject or "Your Analyzt Report")
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"message": f"Report sent to {req.to_email}"}
