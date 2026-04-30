import os
import re
import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils import plan_sub_questions, research_sub_question, synthesize_report
from pdf_export import markdown_to_pdf

load_dotenv()

st.set_page_config(
    page_title="AutoResearch Agent",
    page_icon="🤖",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: #1a2235;
    color: #e2e8f0;
}
.stApp {
    background: linear-gradient(160deg, #1e2d47 0%, #1a2235 50%, #1e293b 100%);
    min-height: 100vh;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 780px; }

.hero { text-align: center; padding: 3rem 1rem 2rem; }
.hero-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0 0%, #38bdf8 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 0.75rem;
}
.hero-sub {
    font-size: 0.95rem;
    color: #94a3b8;
    font-weight: 300;
}

input, textarea, select {
    background-color: #243044 !important;
    color: #e2e8f0 !important;
}
.stTextInput > div > div > input {
    background: #243044 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    caret-color: #38bdf8 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(56, 189, 248, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1) !important;
}
.stTextInput > div > div > input::placeholder { color: #64748b !important; }
.stTextInput label { color: #94a3b8 !important; font-size: 0.8rem !important; letter-spacing: 0.05em; text-transform: uppercase; }

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 2rem !important;
    width: 100%;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

.step-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-left: 3px solid #38bdf8;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: #cbd5e1;
    font-family: 'Space Mono', monospace;
}

.report-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 2rem 2.2rem;
    margin-top: 1rem;
}
.report-box h2 {
    font-size: 1.2rem;
    font-weight: 600;
    color: #38bdf8;
    margin-top: 1.5rem;
    border-bottom: 1px solid rgba(56,189,248,0.2);
    padding-bottom: 0.4rem;
}
.report-box h3 { font-size: 1rem; font-weight: 600; color: #818cf8; margin-top: 1rem; }
.report-box p { color: #cbd5e1; line-height: 1.75; font-size: 0.93rem; }
.report-box ul { color: #cbd5e1; line-height: 1.9; font-size: 0.92rem; }
.report-box strong { color: #e2e8f0; }

.stDownloadButton > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: background 0.2s, border-color 0.2s !important;
}
.stDownloadButton > button:hover {
    background: rgba(56,189,248,0.12) !important;
    border-color: rgba(56,189,248,0.4) !important;
}

hr { border-color: rgba(255,255,255,0.1) !important; }
.stCaption { color: #64748b !important; font-size: 0.75rem !important; text-align: center; }
</style>
""", unsafe_allow_html=True)


def _format_inline(text: str) -> str:
    """Format bold, italic, and URLs into HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Render bare URLs as clickable links
    text = re.sub(
        r'(https?://[^\s\)\]]+)',
        r'<a href="\1" target="_blank" style="color:#38bdf8;text-decoration:underline;word-break:break-all;">\1</a>',
        text
    )
    return text


def _md_to_html(text: str) -> str:
    """Convert basic markdown to HTML for the styled report box."""
    lines = text.splitlines()
    html = []
    in_ul = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_ul: html.append("</ul>"); in_ul = False
            html.append("<br>")
        elif s.startswith("## "):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<h2>{_format_inline(s[3:].strip())}</h2>")
        elif s.startswith("### "):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<h3>{_format_inline(s[4:].strip())}</h3>")
        elif s.startswith("- ") or s.startswith("* "):
            if not in_ul: html.append("<ul>"); in_ul = True
            html.append(f"<li>{_format_inline(s[2:])}</li>")
        elif s.startswith("---"):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append("<hr>")
        else:
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<p>{_format_inline(s)}</p>")
    if in_ul:
        html.append("</ul>")
    return "\n".join(html)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ Agentic AI · Powered by Claude</div>
    <div class="hero-title">AutoResearch<br>Agent</div>
    <div class="hero-sub">Ask any question. Get a full cited report in seconds.</div>
</div>
""", unsafe_allow_html=True)

# ── API key check ─────────────────────────────────────────────────────────────
if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("⚠️ ANTHROPIC_API_KEY not found. Add it to your .env file and restart.")
    st.stop()

# ── Input ─────────────────────────────────────────────────────────────────────
question = st.text_input(
    "RESEARCH QUESTION",
    placeholder="e.g. What are the long-term effects of social media on teenage mental health?",
)

depth = st.slider(
    "RESEARCH DEPTH",
    min_value=1,
    max_value=10,
    value=3,
    help="Higher depth = more sub-questions = more thorough report (and more tokens used)",
)

run = st.button("Run Research →", type="primary", disabled=not question)

# ── Agent loop ────────────────────────────────────────────────────────────────
if run and question:
    st.divider()

    with st.status("🧠 Breaking down your question...", expanded=True) as status:
        sub_questions = plan_sub_questions(question, depth=depth)
        for i, q in enumerate(sub_questions, 1):
            st.markdown(f'<div class="step-card">#{i} &nbsp; {q}</div>', unsafe_allow_html=True)
        status.update(label="✅ Research plan ready", state="complete")

    research_data = {}
    with st.status("🔍 Researching each angle...", expanded=True) as status:
        for i, sub_q in enumerate(sub_questions, 1):
            status.update(label=f"🔍 Researching {i} of {len(sub_questions)}...")
            st.markdown(f'<div class="step-card">Researching: {sub_q}</div>', unsafe_allow_html=True)
            research_data[sub_q] = research_sub_question(sub_q)
        status.update(label="✅ Research complete", state="complete")

    with st.status("📝 Writing your report...", expanded=False) as status:
        report = synthesize_report(question, research_data)
        status.update(label="✅ Report ready", state="complete")

    st.divider()
    st.markdown(f'<div class="report-box">{_md_to_html(report)}</div>', unsafe_allow_html=True)

    Path("outputs").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = question[:40].lower().replace(" ", "_").replace("?", "")
    md_filename = f"outputs/{timestamp}_{slug}.md"
    pdf_filename = f"outputs/{timestamp}_{slug}.pdf"
    full_report = f"# {question}\n\n*Generated by AutoResearch Agent on {datetime.now().strftime('%B %d, %Y')}*\n\n---\n\n{report}"

    with open(md_filename, "w") as f:
        f.write(full_report)
    markdown_to_pdf(question, report, pdf_filename)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("⬇️ Download Markdown", data=full_report,
                           file_name=f"{slug}.md", mime="text/markdown", use_container_width=True)
    with col2:
        with open(pdf_filename, "rb") as f:
            st.download_button("⬇️ Download PDF", data=f.read(),
                               file_name=f"{slug}.pdf", mime="application/pdf", use_container_width=True)
    st.caption("Report saved to outputs/")
