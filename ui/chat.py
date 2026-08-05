import sys
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

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
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
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
        st.session_state.logged_in = True
        st.session_state.user_email = "mockuser@google.com"
        st.session_state.thread_id = "mockuser@google.com"
    else:
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

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

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
    fill: currentColor;
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
    color: var(--teal-dark);
}

.hero-icon svg {
    width: 48px;
    height: 48px;
    fill: currentColor;
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

.content-divider {
    width: 100%;
    max-width: 800px;
    height: 1px;
    background-color: var(--border-color);
    margin: 20px 0;
}

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

/* Secondary Buttons */
.secondary-btn > button {
    background-color: white !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-color) !important;
    padding: 4px 10px !important;
    font-size: 13px !important;
}
.secondary-btn > button:hover {
    background-color: #f3f4f6 !important;
    color: var(--text-main) !important;
}

.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
}
.stTextArea textarea:focus {
    border-color: var(--teal-dark) !important;
    box-shadow: 0 0 0 1px var(--teal-dark) !important;
}

.footer-text {
    font-size: 13px;
    color: var(--text-muted);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

import base64
def get_logo_base64():
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_logo_base64()
LOGO_IMG_TAG = f'<img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 40px; object-fit: contain;">'


def render_top_nav():
    button_label = "Sign out" if st.session_state.logged_in else "Sign in"
    nav_html = f"""
<div class="top-nav">
<div class="nav-left">
{LOGO_IMG_TAG}
<div class="nav-titles" style="margin-left: 10px; justify-content: center;">
<div class="nav-subtitle" style="margin-top: 4px;">Medical question assistant</div>
</div>
</div>
<div class="nav-right">
<div class="sign-out-btn" style="pointer-events: none;">{button_label}</div>
</div>
</div>
"""
    st.markdown(nav_html, unsafe_allow_html=True)

render_top_nav()

if not st.session_state.logged_in:
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
<img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
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
    from db.database import get_user_sessions, create_session, get_session_messages, add_message, rename_session, delete_session, delete_messages_after
    import asyncio
    from agents.orchestrator import run_chat

    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "language" not in st.session_state:
        st.session_state.language = "English"

    # Sidebar for language and timeline
    with st.sidebar:
        st.title("Patient Settings")
        lang_idx = ["English", "Hindi", "Tamil", "Bengali"].index(st.session_state.language) if st.session_state.language in ["English", "Hindi", "Tamil", "Bengali"] else 0
        st.session_state.language = st.selectbox("Preferred Language", ["English", "Hindi", "Tamil", "Bengali"], index=lang_idx)
        
        st.markdown("---")
        st.subheader("Chat History")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()
            
        sessions = get_user_sessions(st.session_state.user_email)
        
        if not sessions:
            st.caption("No past chats.")
        else:
            for s in sessions:
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Make active session slightly bold or different text if possible
                    label = f"**{s['name']}**" if s['id'] == st.session_state.session_id else s['name']
                    if st.button(label, key=f"btn_{s['id']}", use_container_width=True):
                        st.session_state.session_id = s["id"]
                        st.session_state.messages = get_session_messages(s["id"])
                        st.rerun()
                with col2:
                    with st.popover("⋮", use_container_width=True):
                        new_name = st.text_input("Rename Session", value=s["name"], key=f"rn_{s['id']}")
                        if st.button("Save Name", key=f"sv_{s['id']}"):
                            rename_session(s["id"], new_name)
                            st.rerun()
                        st.markdown("---")
                        if st.button("Delete Session", key=f"dl_{s['id']}", type="primary"):
                            delete_session(s["id"])
                            if st.session_state.session_id == s["id"]:
                                st.session_state.session_id = None
                                st.session_state.messages = []
                            st.rerun()

    st.markdown(f"""
<div style="display: flex; flex-direction: column; align-items: center; margin-top: 20px; margin-bottom: 20px;">
    <div style="margin-bottom: 16px; display: flex; justify-content:center; align-items:center;">
        <img src="data:image/png;base64,{LOGO_B64}" alt="Mediate Logo" style="height: 60px; object-fit: contain;">
    </div>
    <div style="font-size: 20px; font-weight: 500; color: var(--text-main);">Wellness & Health Education</div>
</div>
""", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        for idx, msg in enumerate(st.session_state.messages):
            avatar = "👤" if msg["role"] == "user" else "⚕️"
            with st.chat_message(msg["role"], avatar=avatar):
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
                
                # Edit functionality for user messages
                if msg["role"] == "user":
                    with st.popover("Edit"):
                        edited_text = st.text_area("Edit your message:", value=msg["content"], key=f"edit_ta_{idx}")
                        if st.button("Regenerate", key=f"regen_{idx}"):
                            # Truncate history
                            if "id" in msg and msg["id"]:
                                # It's a persisted message, rewind db
                                delete_messages_after(st.session_state.session_id, msg["created_at"])
                            
                            # Truncate session state
                            st.session_state.messages = st.session_state.messages[:idx]
                            
                            # Set the edited query
                            st.session_state.edit_query = edited_text
                            st.rerun()

        # Handle edited query injection
        query = st.chat_input("Ask a wellness or health question...")
        if "edit_query" in st.session_state:
            query = st.session_state.edit_query
            del st.session_state.edit_query

        if query:
            # If no session, create one
            if st.session_state.session_id is None:
                short_title = query[:20] + "..." if len(query) > 20 else query
                st.session_state.session_id = create_session(st.session_state.user_email, name=short_title)
                
            # Add user message to DB and state
            add_message(st.session_state.session_id, "user", query)
            st.session_state.messages = get_session_messages(st.session_state.session_id)
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(query)
            
            with st.chat_message("assistant", avatar="⚕️"):
                with st.spinner("Analyzing and answering…"):
                    try:
                        # Use thread_id as session_id to maintain langgraph memory separation if needed
                        thread_id = st.session_state.session_id
                        
                        answer, citations, mode = asyncio.run(
                            run_chat(
                                message=query,
                                thread_id=thread_id,
                                language=st.session_state.language
                            )
                        )
                        
                        disclaimer = "Educational decision-support output — not medical advice and not a diagnosis."
                        if mode == "emergency":
                            disclaimer = "⚠️ EMERGENCY TRIAGE ACTIVATED. SEEK IMMEDIATE MEDICAL ATTENTION."
                            
                        # Add assistant message to DB
                        add_message(st.session_state.session_id, "assistant", answer, citations=citations, disclaimer=disclaimer)
                        st.session_state.messages = get_session_messages(st.session_state.session_id)
                        
                        st.rerun()
                    except Exception as exc:
                        import traceback
                        st.error(f"An error occurred while answering your question: {exc}")
                        st.code(traceback.format_exc())
