"""tools/emailer.py — Send HTML report emails via the Mailjet API."""

import base64
import html
import json
import os
import re

from mailjet_rest import Client

from app.config import get_env

OUTPUT_DIR = "outputs"


def _md_to_plain(md: str) -> str:
    text = re.sub(r"!\[.*?\]\(.*?\)", "", md)
    text = re.sub(r"^#{1,6}\s+(.+)$", lambda m: m.group(1).upper() + "\n" + "-"*len(m.group(1)), text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", lambda m: m.group(1).upper(), text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^[-*]\s+", "  • ", text, flags=re.MULTILINE)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def _report_html(payload: dict) -> str:
    overview = payload.get("overview") or {}
    findings = payload.get("findings") or []
    summary = payload.get("llm_summary") or ""
    filename = payload.get("filename") or "Dataset"
    generated_at = payload.get("generated_at") or ""

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
            <h2>Top Findings</h2>
            {_findings_to_html(findings)}
          </div>

          <div class="footer">Report by Analyzt</div>
        </div>
      </body>
    </html>
    """
    return html_body


def send_report_email(to_email: str, report_filename: str, subject: str) -> dict:
    api_key = get_env("MAILJET_API_KEY")
    secret_key = get_env("MAILJET_SECRET_KEY")
    sender_email = get_env("MAILJET_SENDER_EMAIL")
    sender_name = get_env("MAILJET_SENDER_NAME", "Analyzt")

    if not api_key:
        return {"success": False, "error": "MAILJET_API_KEY is missing. Set it in Render's environment variables."}
    if not secret_key:
        return {"success": False, "error": "MAILJET_SECRET_KEY is missing. Set it in Render's environment variables."}
    if not sender_email:
        return {"success": False, "error": "MAILJET_SENDER_EMAIL is missing. Set it in Render's environment variables."}

    try:
        payload, md = _load_report_payload(report_filename)
        plain = _md_to_plain(md)
        html_body = _report_html(payload)
    except Exception as e:
        print(f"[emailer] report generation failed: {e}")
        return {"success": False, "error": "Could not generate the report to attach."}

    try:
        path = os.path.join(OUTPUT_DIR, report_filename)
        with open(path, "rb") as f:
            report_b64 = base64.b64encode(f.read()).decode("ascii")
    except Exception as e:
        print(f"[emailer] attachment encoding failed: {e}")
        return {"success": False, "error": "Could not encode the report attachment."}

    data = {
        "Messages": [
            {
                "From": {"Email": sender_email, "Name": sender_name},
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": plain,
                "HTMLPart": html_body,
                "Attachments": [
                    {
                        "ContentType": "text/markdown",
                        "Filename": report_filename,
                        "Base64Content": report_b64,
                    },
                ],
            },
        ],
    }

    try:
        mailjet = Client(auth=(api_key, secret_key), version="v3.1")
        result = mailjet.send.create(data=data)
    except Exception as e:
        print(f"[emailer] Mailjet request failed: {type(e).__name__}")
        return {"success": False, "error": "Failed to reach Mailjet. Please try again."}

    if result.status_code != 200:
        print(f"[emailer] Mailjet API error {result.status_code}: {result.json()}")
        return {
            "success": False,
            "error": f"Mailjet API error ({result.status_code}). Check your API credentials and sender verification.",
        }

    messages = result.json().get("Messages", [])
    message_status = messages[0].get("Status") if messages else None
    if message_status != "success":
        errors = messages[0].get("Errors", []) if messages else []
        print(f"[emailer] Mailjet send not successful: status={message_status} errors={errors}")
        detail = "; ".join(err.get("ErrorMessage", "") for err in errors) or "Mailjet rejected the message."
        return {"success": False, "error": detail}

    return {"success": True, "error": None}
