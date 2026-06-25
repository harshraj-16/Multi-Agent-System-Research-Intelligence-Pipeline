import streamlit as st
import time
import threading
import queue
import sys
import io
from contextlib import redirect_stdout

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0a0a0f;
    color: #e2e2e8;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1100px; margin: 0 auto; }

/* ── Header ── */
.hero {
    text-align: center;
    padding: 3.5rem 0 2.5rem;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 2.5rem;
}
.hero-label {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.22em;
    color: #6c63ff;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #f0f0f8;
    line-height: 1.15;
    margin-bottom: 0.7rem;
}
.hero-title span { color: #6c63ff; }
.hero-sub {
    font-size: 0.95rem;
    color: #6b6b80;
    font-weight: 400;
    letter-spacing: 0.01em;
}

/* ── Input Row ── */
.input-row { display: flex; gap: 0.75rem; margin-bottom: 2.5rem; align-items: flex-end; }

/* Streamlit input override */
.stTextInput > div > div > input {
    background: #12121a !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e2e2e8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
}
.stTextInput label { color: #9090a8 !important; font-size: 0.8rem !important; font-weight: 500 !important; letter-spacing: 0.05em; }

/* Button */
.stButton > button {
    background: #6c63ff !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 2rem !important;
    cursor: pointer !important;
    transition: background 0.2s, transform 0.1s !important;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.stButton > button:hover { background: #5a52e0 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:disabled { background: #2a2a3e !important; color: #4a4a60 !important; cursor: not-allowed !important; }

/* ── Pipeline Steps ── */
.pipeline-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}
.step-card {
    background: #12121a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.1rem 1rem;
    transition: border-color 0.3s, box-shadow 0.3s;
    position: relative;
    overflow: hidden;
}
.step-card.active {
    border-color: #6c63ff;
    box-shadow: 0 0 20px rgba(108,99,255,0.15);
}
.step-card.done {
    border-color: #22c55e;
    box-shadow: 0 0 12px rgba(34,197,94,0.1);
}
.step-card.error {
    border-color: #ef4444;
    box-shadow: 0 0 12px rgba(239,68,68,0.1);
}
.step-icon {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    display: block;
}
.step-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #4a4a60;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.step-name {
    font-size: 0.85rem;
    font-weight: 600;
    color: #c0c0d0;
    margin-bottom: 0.25rem;
}
.step-status {
    font-size: 0.75rem;
    color: #5a5a70;
    font-family: 'JetBrains Mono', monospace;
}
.step-card.active .step-status { color: #6c63ff; }
.step-card.done .step-status { color: #22c55e; }
.step-card.error .step-status { color: #ef4444; }

/* pulse for active */
@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 10px rgba(108,99,255,0.15); }
    50% { box-shadow: 0 0 25px rgba(108,99,255,0.35); }
}
.step-card.active { animation: pulse-border 1.8s ease-in-out infinite; }

/* ── Log Terminal ── */
.terminal-wrap {
    background: #0d0d14;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.5rem;
}
.terminal-header {
    background: #12121a;
    border-bottom: 1px solid #1e1e2e;
    padding: 0.6rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot-r { background: #ef4444; }
.dot-y { background: #f59e0b; }
.dot-g { background: #22c55e; }
.terminal-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4a4a60;
    letter-spacing: 0.1em;
    margin-left: 0.5rem;
}
.terminal-body {
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    line-height: 1.7;
    color: #8888a8;
    min-height: 120px;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}
.log-info { color: #6c63ff; }
.log-ok { color: #22c55e; }
.log-warn { color: #f59e0b; }
.log-err { color: #ef4444; }
.log-dim { color: #4a4a60; }

/* ── Result Sections ── */
.result-section {
    background: #12121a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.2rem;
}
.result-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.85rem 1.2rem;
    border-bottom: 1px solid #1e1e2e;
    background: #0f0f18;
}
.result-icon { font-size: 1rem; }
.result-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #c0c0d0;
    letter-spacing: 0.02em;
}
.result-badge {
    margin-left: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #22c55e;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 4px;
    padding: 0.15rem 0.5rem;
    letter-spacing: 0.05em;
}
.result-body {
    padding: 1.1rem 1.3rem;
    font-size: 0.88rem;
    line-height: 1.75;
    color: #b0b0c8;
}

/* ── Expander overrides ── */
.streamlit-expanderHeader {
    background: #12121a !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 10px !important;
    color: #c0c0d0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #0f0f18 !important;
    border: 1px solid #1e1e2e !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    color: #9898b8 !important;
    font-size: 0.85rem !important;
    line-height: 1.75 !important;
}

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid #1e1e2e;
    margin: 2rem 0;
}

/* ── Spinner override ── */
.stSpinner > div > div { border-top-color: #6c63ff !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #3a3a50;
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
.empty-state-text { font-size: 0.9rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-label">Multi-Agent System</div>
    <div class="hero-title">Research <span>Intelligence</span> Pipeline</div>
    <div class="hero-sub">Search → Scrape → Write → Critique — all automated</div>
</div>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
defaults = {
    "running": False,
    "logs": [],
    "step_states": {1: "idle", 2: "idle", 3: "idle", 4: "idle"},
    "results": {},
    "done": False,
    "error": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

STEPS = [
    (1, "🔍", "Search Agent", "Finds recent information"),
    (2, "📄", "Reader Agent", "Scrapes top sources"),
    (3, "✍️", "Writer Chain",  "Drafts the report"),
    (4, "🧐", "Critic Chain",  "Reviews & scores"),
]

STATUS_LABEL = {"idle": "waiting", "active": "running…", "done": "complete", "error": "failed"}

# ─── Input ────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    topic = st.text_input(
        "RESEARCH TOPIC",
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        disabled=st.session_state.running,
        label_visibility="visible",
    )
with col_btn:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)  # align with input
    run_clicked = st.button(
        "Run Pipeline",
        disabled=st.session_state.running or not topic.strip(),
        use_container_width=True,
    )

# ─── Pipeline Step Cards ──────────────────────────────────────────────────────
def render_steps():
    cols = st.columns(4)
    for (num, icon, name, desc), col in zip(STEPS, cols):
        state = st.session_state.step_states[num]
        with col:
            st.markdown(f"""
            <div class="step-card {state}">
                <span class="step-icon">{icon}</span>
                <div class="step-number">STEP {num:02d}</div>
                <div class="step-name">{name}</div>
                <div class="step-status">{STATUS_LABEL[state]}</div>
            </div>
            """, unsafe_allow_html=True)

steps_placeholder = st.empty()
with steps_placeholder.container():
    render_steps()

# ─── Terminal Log ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="terminal-wrap">
  <div class="terminal-header">
    <span class="dot dot-r"></span>
    <span class="dot dot-y"></span>
    <span class="dot dot-g"></span>
    <span class="terminal-title">AGENT LOG — STDOUT STREAM</span>
  </div>
</div>
""", unsafe_allow_html=True)

log_placeholder = st.empty()

def render_log():
    lines = st.session_state.logs[-120:]  # keep last 120 lines
    html_lines = []
    for ln in lines:
        if ln.startswith("✓") or "complete" in ln.lower() or "done" in ln.lower():
            html_lines.append(f'<span class="log-ok">{ln}</span>')
        elif ln.startswith("→") or "running" in ln.lower() or "working" in ln.lower():
            html_lines.append(f'<span class="log-info">{ln}</span>')
        elif "error" in ln.lower() or "failed" in ln.lower():
            html_lines.append(f'<span class="log-err">{ln}</span>')
        elif ln.startswith("─") or ln.startswith("=") or ln.startswith(" ="):
            html_lines.append(f'<span class="log-dim">{ln}</span>')
        else:
            html_lines.append(ln)
    body = "\n".join(html_lines) if html_lines else '<span class="log-dim">— waiting for pipeline to start —</span>'
    log_placeholder.markdown(
        f'<div class="terminal-body">{body}</div>',
        unsafe_allow_html=True,
    )

render_log()

# ─── Results Placeholder ──────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
results_placeholder = st.empty()

def render_results():
    res = st.session_state.results
    if not res:
        results_placeholder.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🔬</div>
            <div class="empty-state-text">Enter a topic and run the pipeline.<br>Results will appear here as each agent completes.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    with results_placeholder.container():
        if "search_results" in res:
            st.markdown("""
            <div class="result-section">
              <div class="result-header">
                <span class="result-icon">🔍</span>
                <span class="result-title">Search Results</span>
                <span class="result-badge">DONE</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View raw search output", expanded=False):
                st.text(res["search_results"][:3000] + ("…" if len(res["search_results"]) > 3000 else ""))

        if "scraped_content" in res:
            st.markdown("""
            <div class="result-section">
              <div class="result-header">
                <span class="result-icon">📄</span>
                <span class="result-title">Scraped Content</span>
                <span class="result-badge">DONE</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View scraped page content", expanded=False):
                st.text(res["scraped_content"][:3000] + ("…" if len(res["scraped_content"]) > 3000 else ""))

        if "report" in res:
            st.markdown("""
            <div class="result-section">
              <div class="result-header">
                <span class="result-icon">✍️</span>
                <span class="result-title">Final Report</span>
                <span class="result-badge">DONE</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("📋 Read the full report", expanded=True):
                st.markdown(res["report"])

        if "feedback" in res:
            st.markdown("""
            <div class="result-section">
              <div class="result-header">
                <span class="result-icon">🧐</span>
                <span class="result-title">Critic Feedback</span>
                <span class="result-badge">DONE</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("📝 Critic's review", expanded=True):
                st.markdown(res["feedback"])

render_results()

# ─── Pipeline Runner ──────────────────────────────────────────────────────────
def run_pipeline_streaming(topic: str):
    """Run the pipeline and push updates into session_state via a queue."""

    q = queue.Queue()

    class StreamCapture(io.StringIO):
        """Intercept print() calls and push lines to the queue."""
        def write(self, text):
            if text.strip():
                for line in text.splitlines():
                    if line.strip():
                        q.put(("log", line))
            return len(text)

    def worker():
        try:
            from pipeline import run_research_pipeline  # import here so errors surface cleanly

            capture = StreamCapture()
            with redirect_stdout(capture):

                # ── Step 1: Search ──────────────────────────────────────
                q.put(("step", 1, "active"))
                q.put(("log", "→ Search Agent initialising…"))

                from agents import build_search_agent
                search_agent = build_search_agent()
                q.put(("log", "→ Querying for: " + topic))
                search_result = search_agent.invoke({
                    "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
                })
                search_content = search_result['messages'][-1].content
                q.put(("step", 1, "done"))
                q.put(("log", "✓ Search agent complete"))
                q.put(("result", "search_results", search_content))

                # ── Step 2: Reader ──────────────────────────────────────
                q.put(("step", 2, "active"))
                q.put(("log", "→ Reader Agent scraping top URL…"))

                from agents import build_reader_agent
                reader_agent = build_reader_agent()
                reader_result = reader_agent.invoke({
                    "messages": [("user",
                        f"Based on the following search results about '{topic}', "
                        f"pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{search_content[:800]}"
                    )]
                })
                scraped = reader_result['messages'][-1].content
                q.put(("step", 2, "done"))
                q.put(("log", "✓ Reader agent complete"))
                q.put(("result", "scraped_content", scraped))

                # ── Step 3: Writer ──────────────────────────────────────
                q.put(("step", 3, "active"))
                q.put(("log", "→ Writer drafting report…"))

                from agents import writer_chain
                combined = (
                    f"SEARCH RESULTS:\n{search_content}\n\n"
                    f"DETAILED SCRAPED CONTENT:\n{scraped}"
                )
                report = writer_chain.invoke({"topic": topic, "research": combined})
                q.put(("step", 3, "done"))
                q.put(("log", "✓ Writer complete"))
                q.put(("result", "report", report))

                # ── Step 4: Critic ──────────────────────────────────────
                q.put(("step", 4, "active"))
                q.put(("log", "→ Critic reviewing report…"))

                from agents import critic_chain
                feedback = critic_chain.invoke({"report": report})
                q.put(("step", 4, "done"))
                q.put(("log", "✓ Critic complete"))
                q.put(("result", "feedback", feedback))

            q.put(("done",))

        except Exception as exc:
            q.put(("error", str(exc)))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    # ── Drain the queue and re-render ────────────────────────────────────────
    while True:
        try:
            msg = q.get(timeout=0.3)
        except queue.Empty:
            # Nothing new — just re-render to show spinner
            with steps_placeholder.container():
                render_steps()
            render_log()
            if not t.is_alive():
                # Thread died without sending done/error
                st.session_state.error = "Pipeline thread exited unexpectedly."
                break
            continue

        kind = msg[0]

        if kind == "log":
            st.session_state.logs.append(msg[1])

        elif kind == "step":
            _, num, state = msg
            st.session_state.step_states[num] = state

        elif kind == "result":
            _, key, val = msg
            st.session_state.results[key] = val

        elif kind == "done":
            st.session_state.done = True
            st.session_state.running = False
            st.session_state.logs.append("✓ Pipeline finished successfully")
            break

        elif kind == "error":
            st.session_state.error = msg[1]
            st.session_state.running = False
            for s in [1, 2, 3, 4]:
                if st.session_state.step_states[s] == "active":
                    st.session_state.step_states[s] = "error"
            st.session_state.logs.append(f"✗ Error: {msg[1]}")
            break

        # Re-render on every message for live feel
        with steps_placeholder.container():
            render_steps()
        render_log()
        render_results()

    # Final render
    with steps_placeholder.container():
        render_steps()
    render_log()
    render_results()

# ─── Trigger ──────────────────────────────────────────────────────────────────
if run_clicked and topic.strip() and not st.session_state.running:
    # Reset state
    st.session_state.running = True
    st.session_state.done = False
    st.session_state.error = None
    st.session_state.logs = [f"→ Starting pipeline for: {topic}"]
    st.session_state.results = {}
    st.session_state.step_states = {1: "idle", 2: "idle", 3: "idle", 4: "idle"}

    with st.spinner("Pipeline running…"):
        run_pipeline_streaming(topic)

    if st.session_state.error:
        st.error(f"Pipeline failed: {st.session_state.error}")
    else:
        st.success("✓ Research pipeline complete!")

# ─── Error Banner ─────────────────────────────────────────────────────────────
if st.session_state.error and not st.session_state.running:
    st.error(f"Last run error: {st.session_state.error}")
