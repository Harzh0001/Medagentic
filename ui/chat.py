import streamlit as st
from pathlib import Path
import sys as _sys

# --- Make sure `lib.rag` is importable even if Streamlit runs from `ui/`. ---
if str(Path(__file__).resolve().parent.parent) not in _sys.path:
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mediate - Medical question assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Authentication (Google OAuth)
# ─────────────────────────────────────────────────────────────────────────────
import urllib.parse
from config import settings

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

try:
    params = st.query_params
except AttributeError:
    params = st.experimental_get_query_params()

code_param = params.get("code")
if code_param and not st.session_state.logged_in:
    code = code_param[0] if isinstance(code_param, list) else code_param
    
    if not settings.google_client_id:
        # Mock exchange if no credentials exist
        st.session_state.logged_in = True
        st.session_state.user_email = "mockuser@google.com"
        st.session_state.thread_id = "mockuser@google.com"
    else:
        # Real exchange
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
        import requests
        resp = requests.post(token_url, data=token_data)
        if resp.status_code == 200:
            access_token = resp.json().get("access_token")
            # Fetch user info
            user_info_resp = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if user_info_resp.status_code == 200:
                user_info = user_info_resp.json()
                st.session_state.logged_in = True
                st.session_state.user_email = user_info.get("email")
                st.session_state.thread_id = user_info.get("email")
    
    try:
        st.query_params.clear()
    except AttributeError:
        st.experimental_set_query_params()

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Reset and global styles */
:root {
    --bg-color: #f9fafb;
    --text-main: #1f2937;
    --text-muted: #6b7280;
    --teal-dark: #004d40;
    --border-color: #e5e7eb;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-color) !important;
    color: var(--text-main);
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Top Navigation Bar */
.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background-color: white;
    border-bottom: 1px solid var(--border-color);
}

.nav-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background-color: var(--teal-dark);
    border-radius: 50%;
    color: white;
    font-size: 20px;
}
.nav-icon svg {
    width: 24px;
    height: 24px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.nav-titles {
    display: flex;
    flex-direction: column;
}

.nav-brand {
    font-size: 18px;
    font-weight: 500;
    line-height: 1.2;
    color: var(--text-main);
}

.nav-subtitle {
    font-size: 13px;
    color: var(--text-muted);
}

.nav-right .sign-in-btn, .nav-right .sign-out-btn {
    padding: 8px 16px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: white;
    font-weight: 500;
    font-size: 14px;
    color: var(--text-main);
    cursor: pointer;
}

/* Main Content Container */
.main-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 70px);
    padding: 40px 20px;
    text-align: center;
    background-color: var(--bg-color);
}

/* Chat Container */
.chat-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px;
    min-height: calc(100vh - 70px);
    background-color: var(--bg-color);
}
.chat-inner {
    width: 100%;
    max-width: 800px;
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.hero-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    color: var(--text-muted);
}

.hero-icon svg {
    width: 48px;
    height: 48px;
    stroke: currentColor;
    fill: none;
    stroke-width: 1.5;
    stroke-linecap: round;
    stroke-linejoin: round;
}

.hero-title {
    font-size: 20px;
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--text-main);
}

.hero-subtitle {
    font-size: 16px;
    color: var(--text-muted);
    max-width: 600px;
    line-height: 1.5;
    margin-bottom: 48px;
}

/* Divider Line */
.content-divider {
    width: 100%;
    max-width: 800px;
    height: 1px;
    background-color: var(--border-color);
    margin: 20px 0;
}

/* Sign In Card */
.sign-in-card {
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 32px 40px;
    width: 100%;
    max-width: 700px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 24px;
    margin-top: 10px;
}

.sign-in-card-title {
    font-size: 17px;
    font-weight: 400;
    margin-bottom: 24px;
    color: var(--text-main);
}

/* Streamlit button custom style for Google Button */
.stButton > button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: var(--teal-dark) !important;
    color: white !important;
    padding: 10px 24px !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    transition: background-color 0.2s !important;
    border: none !important;
    box-shadow: none !important;
    height: auto !important;
}
.stButton > button:hover {
    background-color: #00362c !important;
    border: none !important;
    color: white !important;
}
.stButton > button:focus {
    box-shadow: none !important;
}

/* Override button for normal actions like 'Ask' */
.chat-inner .stButton > button {
    background-color: white !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-color) !important;
}
.chat-inner .stButton > button:hover {
    background-color: #f3f4f6 !important;
    color: var(--text-main) !important;
}

/* Text area styling */
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
}
.stTextArea textarea:focus {
    border-color: var(--teal-dark) !important;
    box-shadow: 0 0 0 1px var(--teal-dark) !important;
}

/* Footer */
.footer-text {
    font-size: 13px;
    color: var(--text-muted);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Top Nav Component
# ─────────────────────────────────────────────────────────────────────────────
def render_top_nav():
    button_label = "Sign out" if st.session_state.logged_in else "Sign in"
    nav_html = f"""
<div class="top-nav">
<div class="nav-left">
<div class="nav-icon">
<svg viewBox="0 0 24 24">
<path d="M7 17C7 18.6569 8.34315 20 10 20C11.6569 20 13 18.6569 13 17V8M13 8C13 6.34315 14.3431 5 16 5C17.6569 5 19 6.34315 19 8V13C19 15.2091 17.2091 17 15 17H14" />
<circle cx="13" cy="17" r="3" />
</svg>
</div>
<div class="nav-titles">
<div class="nav-brand">Mediate</div>
<div class="nav-subtitle">Medical question assistant</div>
</div>
</div>
<div class="nav-right">
<div class="sign-out-btn" style="pointer-events: none;">{button_label}</div>
</div>
</div>
"""
    st.markdown(nav_html, unsafe_allow_html=True)

render_top_nav()

# ─────────────────────────────────────────────────────────────────────────────
# Render Logic based on Auth State
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    # ─── LOGGED OUT STATE ────────────────────────────────────────────────────
    # Generate OAuth URL or fallback
    if settings.google_client_id:
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.google_client_id}&"
            f"redirect_uri={urllib.parse.quote(settings.google_redirect_uri)}&"
            f"response_type=code&"
            f"scope=openid%20email%20profile"
        )
    else:
        google_auth_url = "?code=mock_code"

    html_hero = f"""
<div class="main-content">
<div class="hero-icon">
<svg viewBox="0 0 24 24">
<path d="M7 17C7 18.6569 8.34315 20 10 20C11.6569 20 13 18.6569 13 17V8M13 8C13 6.34315 14.3431 5 16 5C17.6569 5 19 6.34315 19 8V13C19 15.2091 17.2091 17 15 17H14" />
<circle cx="13" cy="17" r="3" />
</svg>
</div>
<div class="hero-title">Ask a wellness or health education question</div>
<div class="hero-subtitle">Explore wellness topics, health information, and self-care. This educational assistant provides general wellness information and is explicitly not a diagnostic tool.</div>
<div class="content-divider"></div>
<div class="sign-in-card">
<div class="sign-in-card-title">Sign in to start a conversation and save your history.</div>
<a href="{google_auth_url}" target="_self" class="google-btn" style="text-decoration:none;">
    <div class="stButton"><button>Continue with Google</button></div>
</a>
</div>
<div class="footer-text">Mediate provides general information, not medical advice. Always consult a healthcare professional.</div>
</div>
"""
    st.markdown(html_hero, unsafe_allow_html=True)

else:
    # ─── LOGGED IN STATE (CHATBOT) ───────────────────────────────────────────
    
    if "thread_id" not in st.session_state:
        if st.session_state.get("user_email"):
            st.session_state.thread_id = st.session_state.user_email
        else:
            import uuid
            st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    try:
        from db.timeline import get_timeline
        timeline = get_timeline(st.session_state.thread_id)
    except Exception:
        timeline = []

    # Sidebar for language and timeline
    with st.sidebar:
        st.title("Patient Settings")
        st.session_state.language = st.selectbox(
            "Preferred Language",
            ["English", "Hindi", "Tamil", "Bengali"]
        )
        st.markdown("---")
        st.subheader("Symptom Timeline")
        if timeline:
            for item in timeline:
                st.caption(item)
        else:
            st.caption("No symptoms recorded yet.")
            
    st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; margin-top: 20px; margin-bottom: 20px;">
    <div style="color: var(--teal-dark); margin-bottom: 16px;">
        <svg viewBox="0 0 24 24" width="40" height="40">
            <path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M7 17C7 18.6569 8.34315 20 10 20C11.6569 20 13 18.6569 13 17V8M13 8C13 6.34315 14.3431 5 16 5C17.6569 5 19 6.34315 19 8V13C19 15.2091 17.2091 17 15 17H14" />
            <circle cx="13" cy="17" r="3" fill="none" stroke="currentColor" stroke-width="2" />
        </svg>
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Mediate Wellness & Health Education</div>
</div>
""", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "citations" in msg and msg["citations"]:
                    with st.expander(f"Sources ({len(msg['citations'])})"):
                        for c in msg["citations"]:
                            if "url" in c:
                                st.markdown(f"- [{c['title']}]({c['url']})")
                            else:
                                st.markdown(f"- {c['label']} {c['source']} — {c['section']}")
                if "disclaimer" in msg:
                    st.caption(msg["disclaimer"])
        
        query = st.chat_input("Ask a wellness or health question...")
        if query:
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(query)
            st.session_state.messages.append({"role": "user", "content": query})
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing and answering…"):
                    try:
                        # Run LangGraph AI directly inside Streamlit
                        import asyncio
                        from agents.orchestrator import run_chat
                        
                        answer, citations, mode = asyncio.run(
                            run_chat(
                                message=query,
                                thread_id=st.session_state.thread_id,
                                language=st.session_state.language
                            )
                        )
                        
                        # Apply disclaimer
                        disclaimer = "Educational decision-support output — not medical advice and not a diagnosis."
                        if mode == "emergency":
                            disclaimer = "⚠️ EMERGENCY TRIAGE ACTIVATED. SEEK IMMEDIATE MEDICAL ATTENTION."
                            
                        st.markdown(answer)
                        
                        if citations:
                            with st.expander(f"Sources ({len(citations)})"):
                                for c in citations:
                                    if "url" in c:
                                        st.markdown(f"- [{c['title']}]({c['url']})")
                                    else:
                                        st.markdown(f"- {c['label']} {c['source']} — {c['section']}")
                        st.caption(disclaimer)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "citations": citations,
                            "disclaimer": disclaimer
                        })
                        
                        st.rerun() # Refresh to update timeline
                    except Exception as exc:
                        st.error(f"Could not reach the API at localhost:8000.\n{exc}")
