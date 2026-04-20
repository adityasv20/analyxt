"""tools/reporting.py — Markdown report builder plus email metadata."""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from app.models.schemas import DatasetOverview, FindingItem

OUTPUT_DIR = "outputs"


def build_report(
    filename: str,
    overview: Optional[DatasetOverview],
    findings: List[FindingItem],
    chart_paths: List[str],
    llm_summary: str = "",
) -> Tuple[str, str]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Analyzt Report — `{filename}`",
        f"*Generated: {now}*\n",
        "---\n",
    ]

    if overview:
        lines += [
            "## Dataset",
            f"| Property | Value |",
            f"|---|---|",
            f"| Rows | {overview.rows:,} |",
            f"| Columns | {overview.columns} |",
            f"| Numeric | {len(overview.numeric_columns)} |",
            f"| Categorical | {len(overview.categorical_columns)} |",
            f"| Duplicates | {overview.duplicate_rows:,} |",
            f"| Memory | {overview.memory_usage_kb} KB |",
            "",
        ]
        if overview.missing_values:
            lines.append("**Missing values:**")
            for col, count in overview.missing_values.items():
                pct = round(count / overview.rows * 100, 1)
                lines.append(f"- `{col}`: {count} ({pct}%)")
            lines.append("")

    if llm_summary:
        lines += ["## AI Analyst Summary\n", llm_summary, ""]

    if findings:
        lines.append("## Findings\n")
        for f in findings:
            val = f.value if isinstance(f.value, str) else str(f.value)
            note = f" — *{f.note}*" if f.note else ""
            lines.append(f"- **{f.label}:** {val}{note}")
        lines.append("")

    lines += ["---", "*Report by Analyzt*"]
    text = "\n".join(lines)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fname = f"report_{uuid.uuid4().hex[:8]}.md"
    report_path = os.path.join(OUTPUT_DIR, fname)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)

    payload = {
        "filename": filename,
        "generated_at": now,
        "overview": overview.model_dump() if overview else None,
        "findings": [f.model_dump() for f in findings],
        "chart_paths": chart_paths,
        "llm_summary": llm_summary,
        "markdown_path": report_path,
    }
    meta_path = report_path.replace(".md", ".json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)

    return text, fname
