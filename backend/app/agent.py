"""
agent.py — AI provider integration for summaries and grounded chat.

Supports:
  - Gemini via google-generativeai
  - Groq via OpenAI-compatible API
"""

from __future__ import annotations

import re
import time
from typing import List, Optional

import google.generativeai as genai
from openai import OpenAI

from app.config import ENV_PATH, get_env
from app.models.schemas import DatasetOverview, FindingItem

_GEMINI_MODEL: Optional[genai.GenerativeModel] = None
_GROQ_CLIENT: Optional[OpenAI] = None

_GEMINI_MODEL_NAMES = [
    get_env("GEMINI_MODEL", "gemini-2.0-flash"),
    "gemini-2.0-flash-001",
]

_GROQ_MODEL_NAMES = [
    get_env("GROQ_MODEL", "llama-3.1-8b-instant"),
    "llama-3.1-8b-instant",
]

VALID_STEPS = [
    "missing_values",
    "duplicates_check",
    "summary_statistics",
    "outlier_detection",
    "correlation_analysis",
    "categorical_analysis",
    "generate_charts",
]


def _provider() -> str:
    return get_env("AI_PROVIDER", "gemini").lower()


def _get_gemini_model() -> genai.GenerativeModel:
    global _GEMINI_MODEL
    if _GEMINI_MODEL is not None:
        return _GEMINI_MODEL

    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"GEMINI_API_KEY missing or still set to the example value in {ENV_PATH}"
        )

    genai.configure(api_key=api_key)
    last_err = None
    for model_name in _GEMINI_MODEL_NAMES:
        try:
            print(f"[agent] Gemini model: {model_name}")
            _GEMINI_MODEL = genai.GenerativeModel(model_name)
            return _GEMINI_MODEL
        except Exception as e:
            last_err = e
            print(f"[agent] Failed to initialize Gemini model {model_name}: {e}")
    raise RuntimeError(f"Could not initialize any Gemini model from {_GEMINI_MODEL_NAMES}: {last_err}")


def _get_groq_client() -> OpenAI:
    global _GROQ_CLIENT
    if _GROQ_CLIENT is not None:
        return _GROQ_CLIENT

    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"GROQ_API_KEY missing or still set to the example value in {ENV_PATH}"
        )

    _GROQ_CLIENT = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    return _GROQ_CLIENT


def _call_gemini(prompt: str, temperature: float, max_tokens: int) -> str:
    model = _get_gemini_model()
    config = genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)
    for attempt in range(3):
        try:
            return model.generate_content(prompt, generation_config=config).text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                wait = int(re.search(r"retry in (\d+)", str(e)).group(1)) + 1 if re.search(r"retry in (\d+)", str(e)) else 5
                wait = min(wait, 5)
                print(f"[agent] Gemini rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max Gemini retries exceeded")


def _call_groq(prompt: str, temperature: float, max_tokens: int) -> str:
    client = _get_groq_client()
    last_err = None
    for model_name in _GROQ_MODEL_NAMES:
        try:
            print(f"[agent] Groq model: {model_name}")
            response = client.chat.completions.create(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            print(f"[agent] Groq request failed on {model_name}: {e}")
    raise RuntimeError(f"Groq call failed for models {_GROQ_MODEL_NAMES}: {last_err}")


def _call(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    provider = _provider()
    if provider == "groq":
        return _call_groq(prompt, temperature, max_tokens)
    if provider == "gemini":
        return _call_gemini(prompt, temperature, max_tokens)
    raise RuntimeError("AI_PROVIDER must be either 'gemini' or 'groq'")


def plan_analysis(prompt: str, overview: DatasetOverview) -> List[str]:
    """Choose analysis steps locally to avoid burning AI quota on planning."""
    prompt_l = prompt.lower()
    numeric_count = len(overview.numeric_columns)
    categorical_count = len(overview.categorical_columns)

    plan: List[str] = ["summary_statistics"]

    if overview.missing_values:
        plan.append("missing_values")

    if overview.duplicate_rows:
        plan.append("duplicates_check")

    if numeric_count:
        plan.append("outlier_detection")

    if numeric_count >= 2 and any(word in prompt_l for word in ["correlation", "relationship", "pattern", "compare"]):
        plan.append("correlation_analysis")

    if categorical_count and any(word in prompt_l for word in ["category", "categorical", "group", "segment", "breakdown"]):
        plan.append("categorical_analysis")

    if numeric_count >= 2 and "correlation_analysis" not in plan:
        plan.append("correlation_analysis")

    if categorical_count and "categorical_analysis" not in plan:
        plan.append("categorical_analysis")

    plan.append("generate_charts")
    deduped_plan = list(dict.fromkeys(step for step in plan if step in VALID_STEPS))
    print(f"[agent] Local plan: {deduped_plan}")
    return deduped_plan


def generate_summary(
    prompt: str,
    overview: DatasetOverview,
    findings: List[FindingItem],
    chart_count: int,
) -> str:
    """Write a concise, high-signal analyst summary."""
    stats_lines = []
    for f in findings:
        if f.label.startswith("Stats:") and isinstance(f.value, dict):
            col = f.label.replace("Stats: ", "")
            v = f.value
            stats_lines.append(
                f"  {col}: mean={v.get('mean')}, median={v.get('median')}, "
                f"min={v.get('min')}, max={v.get('max')}, std={v.get('std')}"
            )

    findings_text = "\n".join([
        f"- {f.label}: {f.value}" + (f" | {f.note}" if f.note else "")
        for f in findings
    ])

    system = f"""You are a senior data analyst. Write a concise insight report — NO FILLER, HIGH SIGNAL.

STRICT FORMAT — use exactly these markdown headings:

## Key Findings
3–4 bullet points. Each must cite a specific number or column name. Start each with a bold label.

## Data Quality
1–2 sentences only. Mention missing values, duplicates, and outliers with exact counts if available.

## Patterns
2–3 sentences on correlations, distributions, or anomalies. Be specific.

## Recommendations
3 actionable bullets. Reference specific columns.

RULES:
- Target 160–220 words total
- No intro sentences like "This dataset contains..." — start directly with findings
- No vague phrases like "further analysis may be needed"
- Reference actual column names and numbers from the findings below

---
User asked: "{prompt}"
Dataset: {overview.rows:,} rows × {overview.columns} cols
Numeric columns: {overview.numeric_columns}
Categorical columns: {overview.categorical_columns}
Charts generated: {chart_count}

Numeric stats:
{chr(10).join(stats_lines) or "  (none)"}

All findings:
{findings_text}
---

Write the report now:"""

    try:
        return _call(system, temperature=0.25, max_tokens=420)
    except Exception as e:
        return f"⚠ Summary unavailable: {e}"


def grounded_call(context: str, question: str, history: str = "") -> str:
    prompt = f"""You are a data analyst assistant. Answer using ONLY the dataset information below.
If the answer isn't in the data, say so clearly.

DATASET CONTEXT:
{context}
{history}

QUESTION: {question}

Rules:
- Reference specific numbers and column names
- Use markdown: **bold** key values, bullet lists for multiple items
- Max 180 words
- If unavailable in the data, say: "This isn't available in the uploaded dataset."

Answer:"""
    return _call(prompt, temperature=0.2, max_tokens=260)
