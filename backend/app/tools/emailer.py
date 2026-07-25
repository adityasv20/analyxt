"""tools/emailer.py — Send HTML report emails via SMTP."""

import html
import json
import os
import re
import smtplib
import socket
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import ENV_PATH, get_env

_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Some hosts (e.g. Render) lack outbound IPv6 routes; smtplib's default
    dual-stack lookup can pick an unreachable AAAA record and fail with
    [Errno 101] Network is unreachable. Force IPv4 resolution instead."""
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

OUTPUT_DIR = "outputs"
CHART_LABELS = {
    "hist": "Distribution",
    "corr": "Correlation Matrix",
    "cat": "Category Breakdown",
    "box": "Box Plot",
    "scatter": "Scatter Plot",
    "missing": "Missing Values",
}


def _md_to_plain(md: str) -> str:
    text = re.sub(r"!\[.*?\]\(.*?\)", "", md)
    text = re.sub(r"^#{1,6}\s+(.+)$", lambda m: m.group(1).upper() + "\n" + "-"*len(m.group(1)), text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", lambda m: m.group(1).upper(), text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^[-*]\s+", "  • ", text, flags=re.MULTILINE)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chart_label(path: str) -> str:
    stem = os.path.basename(path).split("_")[0]
    return CHART_LABELS.get(stem, stem.title())


def _load_report_payload(report_filename: str) -> tuple[dict, str]:
    md_path = os.path.join(OUTPUT_DIR, report_filename)
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Report not found: {report_filename}")

    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    meta_path = md_path.replace(".md", ".json")
    payload = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    return payload, md


def _summary_to_html(summary: str) -> str:
    if not summary:
        return "<p>No AI summary was available for this report.</p>"

    blocks = []
    current_list = []
    for raw_line in summary.splitlines():
        line = raw_line.strip()
        if not line:
            if current_list:
                blocks.append("<ul>" + "".join(current_list) + "</ul>")
                current_list = []
            continue

        if line.startswith("## "):
            if current_list:
                blocks.append("<ul>" + "".join(current_list) + "</ul>")
                current_list = []
            blocks.append(f"<h3>{html.escape(line[3:])}</h3>")
            continue

        if line.startswith(("- ", "* ")):
            item = html.escape(line[2:])
            item = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", item)
            current_list.append(f"<li>{item}</li>")
            continue

        if current_list:
            blocks.append("<ul>" + "".join(current_list) + "</ul>")
            current_list = []
        paragraph = html.escape(line)
        paragraph = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", paragraph)
        blocks.append(f"<p>{paragraph}</p>")

    if current_list:
        blocks.append("<ul>" + "".join(current_list) + "</ul>")
    return "".join(blocks)


def _findings_to_html(findings: list[dict], limit: int = 12) -> str:
    if not findings:
        return "<p>No findings were captured.</p>"

    rows = []
    for finding in findings[:limit]:
        label = html.escape(str(finding.get("label", "")))
        value = finding.get("value", "")
        note = html.escape(str(finding.get("note", ""))) if finding.get("note") else ""
        if isinstance(value, dict):
            value_html = "<br>".join(
                f"<span><strong>{html.escape(str(k))}:</strong> {html.escape(str(v))}</span>"
                for k, v in value.items()
            )
        else:
            value_html = html.escape(str(value))
        note_html = f"<div class='finding-note'>{note}</div>" if note else ""
        rows.append(
            f"<div class='finding-row'><div class='finding-label'>{label}</div>"
            f"<div class='finding-value'>{value_html}{note_html}</div></div>"
        )
    return "".join(rows)


def _charts_to_html(chart_paths: list[str]) -> tuple[str, list[tuple[str, str]]]:
    if not chart_paths:
        return "<p>No charts were generated for this report.</p>", []

    parts = []
    attachments = []
    for idx, chart_path in enumerate(chart_paths[:6], start=1):
        local_path = chart_path.lstrip("/")
        cid = f"chart_{idx}"
        attachments.append((cid, local_path))
        parts.append(
            "<div class='chart-card'>"
            f"<div class='chart-title'>{html.escape(_chart_label(chart_path))}</div>"
            f"<img src='cid:{cid}' alt='{html.escape(_chart_label(chart_path))}' />"
            "</div>"
        )
    return "".join(parts), attachments


def _report_html(payload: dict) -> tuple[str, list[tuple[str, str]]]:
    overview = payload.get("overview") or {}
    findings = payload.get("findings") or []
    chart_paths = payload.get("chart_paths") or []
    summary = payload.get("llm_summary") or ""
    filename = payload.get("filename") or "Dataset"
    generated_at = payload.get("generated_at") or ""

    charts_html, chart_attachments = _charts_to_html(chart_paths)

    missing = overview.get("missing_values") or {}
    missing_html = "".join(
        f"<span class='chip'>{html.escape(col)}: {count}</span>"
        for col, count in missing.items()
    ) or "<span class='chip'>No missing values</span>"

    html_body = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{
            margin: 0;
            padding: 0;
            background: #edf4fb;
            font-family: Arial, sans-serif;
            color: #102033;
          }}
          .shell {{
            max-width: 960px;
            margin: 0 auto;
            padding: 28px 18px 40px;
          }}
          .hero {{
            background: linear-gradient(135deg, #0f172a 0%, #0b3954 48%, #ea580c 100%);
            color: #f8fbff;
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
          }}
          .eyebrow {{
            font-size: 11px;
            letter-spacing: 0.24em;
            text-transform: uppercase;
            opacity: 0.72;
          }}
          .title {{
            font-size: 32px;
            line-height: 1.1;
            margin: 10px 0 6px;
            font-weight: 700;
          }}
          .meta {{
            font-size: 14px;
            color: rgba(248, 251, 255, 0.86);
          }}
          .grid {{
            margin-top: 18px;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
          }}
          .stat {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            padding: 14px;
          }}
          .stat-value {{
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
          }}
          .stat-label {{
            margin-top: 6px;
            font-size: 11px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: rgba(248, 251, 255, 0.72);
          }}
          .section {{
            margin-top: 18px;
            background: #ffffff;
            border-radius: 22px;
            padding: 24px;
            box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
          }}
          .section h2 {{
            margin: 0 0 14px;
            font-size: 20px;
            color: #0f172a;
          }}
          .section h3 {{
            margin: 18px 0 8px;
            font-size: 15px;
            color: #0b3954;
          }}
          .section p, .section li {{
            font-size: 14px;
            line-height: 1.65;
            color: #334155;
          }}
          .chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }}
          .chip {{
            display: inline-block;
            padding: 8px 10px;
            border-radius: 999px;
            background: #eff6ff;
            color: #0b3954;
            font-size: 12px;
            border: 1px solid #cfe4f7;
          }}
          .finding-row {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 14px;
            padding: 12px 0;
            border-top: 1px solid #e6edf5;
          }}
          .finding-row:first-child {{
            border-top: 0;
            padding-top: 0;
          }}
          .finding-label {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #0b3954;
          }}
          .finding-value {{
            font-size: 14px;
            line-height: 1.6;
            color: #334155;
          }}
          .finding-note {{
            margin-top: 4px;
            font-size: 12px;
            color: #64748b;
          }}
          .charts {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
          }}
          .chart-card {{
            background: #f8fbff;
            border: 1px solid #dce8f3;
            border-radius: 18px;
            padding: 12px;
          }}
          .chart-title {{
            font-size: 13px;
            font-weight: 700;
            color: #0b3954;
            margin-bottom: 10px;
          }}
          .chart-card img {{
            width: 100%;
            border-radius: 12px;
            display: block;
          }}
          .footer {{
            margin-top: 14px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
          }}
        </style>
      </head>
      <body>
        <div class="shell">
          <div class="hero">
            <div class="eyebrow">Analyzt Report</div>
            <div class="title">{html.escape(filename)}</div>
            <div class="meta">Generated {html.escape(generated_at)}</div>
            <div class="grid">
              <div class="stat"><div class="stat-value">{overview.get("rows", 0):,}</div><div class="stat-label">Rows</div></div>
              <div class="stat"><div class="stat-value">{overview.get("columns", 0)}</div><div class="stat-label">Columns</div></div>
              <div class="stat"><div class="stat-value">{len(overview.get("numeric_columns", []))}</div><div class="stat-label">Numeric</div></div>
              <div class="stat"><div class="stat-value">{len(overview.get("categorical_columns", []))}</div><div class="stat-label">Categorical</div></div>
            </div>
          </div>

          <div class="section">
            <h2>Dataset Snapshot</h2>
            <div class="chips">
              <span class="chip">Duplicates: {overview.get("duplicate_rows", 0):,}</span>
              <span class="chip">Memory: {overview.get("memory_usage_kb", 0)} KB</span>
            </div>
            <h3>Missing Values</h3>
            <div class="chips">{missing_html}</div>
          </div>

          <div class="section">
            <h2>AI Analyst Summary</h2>
            {_summary_to_html(summary)}
          </div>

          <div class="section">
            <h2>Charts</h2>
            <div class="charts">{charts_html}</div>
          </div>

          <div class="section">
            <h2>Top Findings</h2>
            {_findings_to_html(findings)}
          </div>

          <div class="footer">Report by Analyzt</div>
        </div>
      </body>
    </html>
    """
    return html_body, chart_attachments


def send_report_email(to_email: str, report_filename: str, subject: str) -> dict:
    smtp_host = get_env("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(get_env("SMTP_PORT", "587"))
    smtp_user = get_env("SMTP_USER")
    smtp_pass = get_env("SMTP_PASS")

    if not smtp_user or not smtp_pass:
        return {
            "success": False,
            "error": f"SMTP credentials missing or still set to the example values in {ENV_PATH}",
        }

    try:
        payload, md = _load_report_payload(report_filename)
        plain = _md_to_plain(md)
        html_body, chart_attachments = _report_html(payload)

        msg = MIMEMultipart("mixed")
        msg["From"], msg["To"], msg["Subject"] = smtp_user, to_email, subject

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(plain, "plain", "utf-8"))
        related = MIMEMultipart("related")
        related.attach(MIMEText(html_body, "html", "utf-8"))
        for cid, chart_path in chart_attachments:
            if not os.path.exists(chart_path):
                continue
            with open(chart_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=os.path.basename(chart_path))
                related.attach(img)
        alt.attach(related)
        msg.attach(alt)

        path = os.path.join(OUTPUT_DIR, report_filename)
        with open(path, "rb") as f:
            att = MIMEBase("text", "markdown")
            att.set_payload(f.read())
            encoders.encode_base64(att)
            att.add_header("Content-Disposition", f'attachment; filename="{report_filename}"')
            msg.attach(att)

        socket.getaddrinfo = _ipv4_only_getaddrinfo
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
                s.ehlo(); s.starttls(); s.login(smtp_user, smtp_pass)
                s.sendmail(smtp_user, to_email, msg.as_string())
        finally:
            socket.getaddrinfo = _orig_getaddrinfo

        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}
