import os
import threading
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from loguru import logger

from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.engine import AgentEngine
from digital_humain.core.llm import OllamaProvider, OpenRouterProvider, LettaProvider
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.utils.config import load_config

# Load .env for API keys
load_dotenv()

st.set_page_config(
    page_title="Digital Humain Console",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for a high-contrast dark theme reminiscent of Letta ---
st.markdown(
    """
    <style>
    :root {
      --bg: #0b0d12;
      --panel: #111725;
      --panel-2: #0f1522;
      --text: #e9eef7;
      --muted: #a3b7d8;
      --accent: #4dd0ff;
      --success: #4cd964;
      --warning: #ffc260;
      --error: #ff6b6b;
    }
    body, .stApp { background: var(--bg); color: var(--text); }
    .stButton>button { background: var(--panel-2); color: var(--text); border: 1px solid var(--accent); }
    .stTextInput>div>div>input, textarea, .stSelectbox>div>div { background: var(--panel); color: var(--text); }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .panel { padding: 1rem; border: 1px solid #1f2a3d; border-radius: 10px; background: var(--panel); }
    .panel-title { font-weight: 600; color: var(--accent); letter-spacing: 0.02em; }
    .log-box { background: var(--panel-2); color: var(--text); border-radius: 10px; border: 1px solid #1f2a3d; padding: 0.75rem; height: 460px; overflow-y: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session state helpers ---
def ensure_state():
    defaults = {
        "logs": [],
        "agent_thread": None,
        "cancel_event": None,
        "task": "Go to notepad and write a letter to Steve Jobs in 10 words",
        "provider": "openrouter",
        "model": "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
        "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "letta_key": os.environ.get("LETTA_API_KEY", ""),
        "letta_agent_id": os.environ.get("LETTA_AGENT_ID", ""),
        "recursion_limit": 15,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def append_log(msg: str):
    st.session_state.logs.append(msg)


def build_llm(provider: str, model: str, config: dict, api_key: str) -> object:
    if provider == "openrouter":
        or_cfg = config.get("llm", {}).get("openrouter", {})
        key = api_key.strip() or os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is missing. Set it in .env or the UI field.")
        return OpenRouterProvider(
            model=model,
            api_key=key,
            base_url=or_cfg.get("base_url", "https://openrouter.ai/api/v1"),
            timeout=or_cfg.get("timeout", 120),
            referer=or_cfg.get("referer"),
            site_url=or_cfg.get("site_url"),
        )
    if provider == "letta":
        let_cfg = config.get("llm", {}).get("letta", {})
        key = api_key.strip() or os.environ.get("LETTA_API_KEY", "")
        agent_id = st.session_state.get("letta_agent_id") or os.environ.get("LETTA_AGENT_ID", "")
        if not key or not agent_id:
            raise RuntimeError("Letta requires LETTA_API_KEY and LETTA_AGENT_ID (via .env or UI).")
        return LettaProvider(
            agent_id=agent_id,
            api_key=key,
            base_url=let_cfg.get("base_url", "https://api.letta.ai"),
            timeout=let_cfg.get("timeout", 120),
            model=model,
        )
    # Default to Ollama
    return OllamaProvider(
        model=model,
        base_url=config.get("llm", {}).get("base_url", "http://localhost:11434"),
        timeout=config.get("llm", {}).get("timeout", 300),
    )


def run_agent(task: str, provider: str, model: str, api_key: str, recursion_limit: int, cancel_event: threading.Event):
    try:
        config = load_config()
        append_log(f"Starting task with provider={provider}, model={model}")

        llm = build_llm(provider, model, config, api_key)
        screen_analyzer = ScreenAnalyzer(save_screenshots=True, screenshot_dir="./screenshots")
        gui_actions = GUIActions(pause=1.0)

        tool_registry = ToolRegistry()
        tool_registry.register(FileReadTool())
        tool_registry.register(FileWriteTool())
        tool_registry.register(FileListTool())

        agent_config = AgentConfig(
            name="web_agent",
            role=AgentRole.EXECUTOR,
            model=model,
            max_iterations=recursion_limit,
        )

        agent = DesktopAutomationAgent(
            config=agent_config,
            llm_provider=llm,
            screen_analyzer=screen_analyzer,
            gui_actions=gui_actions,
            tool_registry=tool_registry,
        )

        engine = AgentEngine(agent, cancel_event=cancel_event)
        engine.build_graph()

        result = engine.run(task, recursion_limit=recursion_limit)

        if result.get("error"):
            append_log(f"❌ Task failed: {result['error']}")
        else:
            append_log("✅ Task completed successfully")
    except Exception as e:
        append_log(f"❌ Execution error: {e}")
    finally:
        st.session_state.agent_thread = None
        st.session_state.cancel_event = None


# --- UI Layout ---
ensure_state()
st.title("Digital Humain Console")
st.caption("Modern web UI for desktop automation agents")

left, center, right = st.columns([1.2, 1.6, 1.2])

with left:
    st.markdown("<div class='panel-title'>Agent Settings</div>", unsafe_allow_html=True)
    with st.container():
        st.selectbox("Provider", ["ollama", "openrouter", "letta"], key="provider")
        st.text_input("Model", key="model")
        st.number_input("Recursion limit", min_value=5, max_value=50, value=st.session_state.recursion_limit, key="recursion_limit")
        if st.session_state.provider == "openrouter":
            st.text_input("OpenRouter API Key", type="password", key="openrouter_key")
        if st.session_state.provider == "letta":
            st.text_input("Letta API Key", type="password", key="letta_key")
            st.text_input("Letta Agent ID", key="letta_agent_id")

    st.markdown("<div class='panel-title' style='margin-top:0.8rem'>Task</div>", unsafe_allow_html=True)
    st.text_area("", key="task", height=140)

    start = st.button("Run", type="primary")
    stop = st.button("Stop", disabled=st.session_state.agent_thread is None)

    if start and st.session_state.agent_thread is None:
        st.session_state.cancel_event = threading.Event()
        t = threading.Thread(
            target=run_agent,
            args=(
                st.session_state.task,
                st.session_state.provider,
                st.session_state.model,
                st.session_state.openrouter_key if st.session_state.provider == "openrouter" else st.session_state.letta_key,
                st.session_state.recursion_limit,
                st.session_state.cancel_event,
            ),
            daemon=True,
        )
        st.session_state.agent_thread = t
        t.start()
        append_log("▶️ Task started")

    if stop and st.session_state.cancel_event:
        st.session_state.cancel_event.set()
        append_log("⏹ Stop requested")

with center:
    st.markdown("<div class='panel-title'>Console</div>", unsafe_allow_html=True)
    st.markdown("<div class='log-box'>" + "<br>".join(st.session_state.logs[-400:]) + "</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='panel-title'>Memory & Status</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>" +
                f"<b>Agent Thread:</b> {'running' if st.session_state.agent_thread else 'idle'}<br>" +
                f"<b>Provider:</b> {st.session_state.provider}<br>" +
                f"<b>Model:</b> {st.session_state.model}<br>" +
                f"<b>Recursion Limit:</b> {st.session_state.recursion_limit}<br>" +
                "</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0.8rem'>Shortcuts</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>Run: launch a task.<br>Stop: send a cancel signal.<br>Models: enter any allowed model string for the chosen provider.</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("Need more? Extend this page with recordings, episodic memory stats, and richer logs.")
