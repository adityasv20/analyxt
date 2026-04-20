"""
tools/chat_engine.py — Grounded dataset Q&A engine.

Hybrid strategy:
  1. Pandas-first: deterministic answers for recognizable analytical patterns
  2. AI fallback: grounded in compact dataset context (schema + stats + samples)
"""

import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd

UPLOAD_DIR = "uploads"


def _load(filename: str) -> pd.DataFrame:
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset '{filename}' not found.")
    return pd.read_csv(path)


def _numeric(df): return df.select_dtypes(include="number").columns.tolist()
def _cats(df):    return df.select_dtypes(include=["object","category"]).columns.tolist()

def _find(df, keywords):
    for kw in keywords:
        for col in df.columns:
            if kw.lower() in col.lower():
                return col
    return None

def _price_col(df): return _find(df, ["price","cost","value","sale","amount","revenue","salary","income","fare"])
def _loc_col(df):   return _find(df, ["city","town","state","region","country","location","area","place","district"])
def _date_col(df):  return _find(df, ["year","date","month","time","period","quarter"])
def _name_col(df):  return _find(df, ["name","product","item","category","brand","type"])


# ── Pandas answer functions ───────────────────────────────────────────────────

def _cheapest_expensive(df, q) -> Optional[str]:
    price = _price_col(df)
    if not price: return None
    group = _loc_col(df) or _name_col(df)

    if not group:
        mn, mx = df[price].min(), df[price].max()
        return (
            f"**{price} summary:**\n\n"
            f"- Min: **{mn:,.2f}**\n- Max: **{mx:,.2f}**\n"
            f"- Mean: **{df[price].mean():,.2f}**\n- Median: **{df[price].median():,.2f}**"
        )

    g = df.groupby(group)[price].agg(["median","mean","count"]).round(2).sort_values("median")
    want_exp = any(w in q for w in ["expens","highest","maximum","costly","most"])
    table = g.tail(5).iloc[::-1] if want_exp else g.head(5)
    label = f"{'Most expensive' if want_exp else 'Cheapest'} by {group} (median {price})"
    rows = "\n".join([f"- **{idx}**: median={r['median']:,.2f}, n={int(r['count'])}"
                      for idx, r in table.iterrows()])
    return f"**{label}:**\n\n{rows}"


def _time_trend(df, q) -> Optional[str]:
    date = _date_col(df)
    if not date: return None
    val = _price_col(df) or (_numeric(df)[0] if _numeric(df) else None)
    if not val: return None

    g = df.groupby(date)[val].mean().round(2).sort_values(ascending=False)
    want_low = any(w in q for w in ["lowest","worst","minimum","min","bottom"])
    top = g.tail(5).sort_values() if want_low else g.head(5)
    label = f"{'Lowest' if want_low else 'Highest'} avg {val} by {date}"
    rows = "\n".join([f"- **{idx}**: {v:,.2f}" for idx, v in top.items()])
    best, worst = g.index[0], g.index[-1]
    return (f"**{label}:**\n\n{rows}\n\n"
            f"Peak: **{best}** ({g.iloc[0]:,.2f}) · Lowest: **{worst}** ({g.iloc[-1]:,.2f})")


def _correlation(df, q) -> Optional[str]:
    num = _numeric(df)
    if len(num) < 2: return None
    target = next((c for c in num if c.lower() in q), None) or _price_col(df) or num[0]
    corr = df[num].corr()[target].drop(target).sort_values(key=abs, ascending=False).head(8)
    rows = "\n".join([f"- **{c}**: r={v:+.3f} ({'pos' if v>0 else 'neg'})" for c, v in corr.items()])
    strong = [c for c, v in corr.items() if abs(v) >= 0.5]
    note = f"\n\n**Strongly related** (|r|≥0.5): {', '.join(strong)}" if strong else ""
    return f"**Correlations with `{target}`:**\n\n{rows}{note}"


def _column_stats(df, q) -> Optional[str]:
    for col in df.columns:
        if col.lower() in q:
            if col in _numeric(df):
                s = df[col].describe()
                return (f"**`{col}` statistics:**\n\n"
                        f"- Mean: **{s['mean']:,.4f}**\n- Median: **{df[col].median():,.4f}**\n"
                        f"- Std: **{s['std']:,.4f}**\n- Min: **{s['min']:,.4f}** · Max: **{s['max']:,.4f}**\n"
                        f"- Nulls: **{df[col].isna().sum():,}**")
            elif col in _cats(df):
                top = df[col].value_counts().head(8)
                rows = "\n".join([f"- **{v}**: {c:,} ({c/len(df)*100:.1f}%)" for v, c in top.items()])
                return f"**Top values in `{col}`** ({df[col].nunique()} unique):\n\n{rows}"
    return None


def _count_info(df, q) -> Optional[str]:
    if not any(w in q for w in ["how many","count","number of","total","size","shape"]):
        return None
    return (f"**Dataset size:**\n\n- Rows: **{len(df):,}**\n- Columns: **{len(df.columns)}**\n"
            f"- Missing cells: **{df.isnull().sum().sum():,}**\n"
            f"- Complete rows: **{df.dropna().shape[0]:,}**\n\n"
            f"Columns: {', '.join(f'`{c}`' for c in df.columns)}")


def _top_bottom(df, q) -> Optional[str]:
    import re
    m = re.search(r"\b(top|bottom|best|worst)\s*(\d+)\b", q)
    n = int(m.group(2)) if m else 5
    direction = m.group(1) if m else "top"
    num = _numeric(df)
    if not num: return None

    sort_col = next((c for c in num if c.lower() in q), None) or _price_col(df) or num[0]
    asc = direction in ("bottom", "worst")
    result = df.nsmallest(n, sort_col) if asc else df.nlargest(n, sort_col)

    display = [sort_col]
    for c in [_loc_col(df), _name_col(df), _date_col(df)]:
        if c and c not in display: display.append(c)

    rows = [f"{i+1}. " + " · ".join(f"{c}={row[c]}" for c in display if c in row.index)
            for i, (_, row) in enumerate(result.iterrows())]
    return f"**{direction.title()} {n} by {sort_col}:**\n\n" + "\n".join(rows)


def _try_pandas(df: pd.DataFrame, q: str) -> Optional[str]:
    """Route question to the right pandas function. Returns None if no match."""
    q = q.lower()

    if any(w in q for w in ["how many","count","number of","total rows","size"]):
        r = _count_info(df, q); return r if r else None

    if any(w in q for w in ["correlat","related to","affect","predict","associat","influenc"]):
        return _correlation(df, q)

    if any(w in q for w in ["cheap","expens","afford","lowest price","highest price","cost"]):
        return _cheapest_expensive(df, q)

    if any(w in q for w in ["year","month","period","trend","over time","which year","when","peak"]):
        return _time_trend(df, q)

    if any(w in q for w in ["statistic","average","mean","median","distribution","range","describe"]):
        return _column_stats(df, q)

    if any(w in q for w in ["top ","bottom ","best ","worst ","show me","list the","highest","lowest","rank"]):
        return _top_bottom(df, q)

    # Column-name match — try stats for any mentioned column
    for col in df.columns:
        if col.lower() in q:
            r = _column_stats(df, q)
            if r: return r

    return None


def _build_context(df: pd.DataFrame) -> str:
    lines = [
        f"Dataset: {len(df):,} rows × {len(df.columns)} columns",
        f"Columns: {', '.join(df.columns)}",
        f"Numeric: {', '.join(_numeric(df)) or 'none'}",
        f"Categorical: {', '.join(_cats(df)) or 'none'}",
        "",
        "Numeric statistics:",
    ]
    for col in _numeric(df)[:8]:
        s = df[col].describe()
        lines.append(f"  {col}: mean={s['mean']:.2f}, median={df[col].median():.2f}, "
                     f"min={s['min']:.2f}, max={s['max']:.2f}, nulls={df[col].isna().sum()}")

    if _cats(df):
        lines.append("\nTop categorical values:")
        for col in _cats(df)[:4]:
            top = df[col].value_counts().head(5)
            lines.append(f"  {col}: {', '.join(f'{v}({c})' for v,c in top.items())}")

    lines.append("\nFirst 5 rows:")
    lines.append(df.head(5).to_string(index=False))
    return "\n".join(lines)


# ── Main entry point ──────────────────────────────────────────────────────────

def answer_question(filename: str, question: str, history: list) -> Tuple[str, str]:
    df = _load(filename)

    # Step 1: deterministic pandas answer
    pandas_ans = _try_pandas(df, question)
    if pandas_ans:
        return pandas_ans, "pandas"

    # Step 2: grounded AI answer
    context = _build_context(df)
    history_text = ""
    if history:
        recent = history[-6:]
        history_text = "\nPrevious conversation:\n" + "\n".join([
            f"{'User' if m['role']=='user' else 'Assistant'}: {m['content']}"
            for m in recent
        ])

    from app.agent import grounded_call
    answer = grounded_call(context, question, history_text)
    return answer, "ai"
