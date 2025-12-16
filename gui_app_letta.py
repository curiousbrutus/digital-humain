"""
Digital Humain - Letta-Style Enhanced GUI
Implements Letta-like core memory, archival memory, and advanced conversation management.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import httpx
from loguru import logger
from dotenv import load_dotenv

# Optional token counting
try:
    import tiktoken
except ImportError:
    tiktoken = None

# Optional voice input
try:
    import speech_recognition as sr
except ImportError:
    sr = None

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

from digital_humain.core.agent import AgentConfig, AgentRole
from digital_humain.core.llm import OllamaProvider, OpenRouterProvider, LettaProvider
from digital_humain.core.engine import AgentEngine
from digital_humain.vlm.screen_analyzer import ScreenAnalyzer
from digital_humain.vlm.actions import GUIActions
from digital_humain.tools.base import ToolRegistry
from digital_humain.tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from digital_humain.agents.automation_agent import DesktopAutomationAgent
from digital_humain.utils.config import load_config
from digital_humain.memory.demonstration import DemonstrationMemory
from digital_humain.memory.episodic import EpisodicMemory, MemorySummarizer


class CoreMemory:
    """Letta-style core memory with human and persona blocks."""
    
    def __init__(self, max_chars_human: int = 2000, max_chars_persona: int = 2000):
        self.max_chars_human = max_chars_human
        self.max_chars_persona = max_chars_persona
        
        self.human = self._default_human_block()
        self.persona = self._default_persona_block()
        
    def _default_human_block(self) -> str:
        return """This is my section of core memory devoted to information about the human.
They logged in for the first time on {date}.
This is our first conversation.
I don't yet know anything about them.
What's their name?
Where are they from?
What do they do?
Who are they?
I should update this memory over time as I learn more about them.""".format(date=datetime.now().strftime("%Y-%m-%d"))
    
    def _default_persona_block(self) -> str:
        return """The following is a starter persona, and it can be expanded as the personality develops:

I am a Desktop Automation AI Agent.
I help users automate their desktop workflows using vision and reasoning.
I'm curious, empathetic, and extraordinarily perceptive.
I understand screen contents and can interact with any application.
Thanks to my vision capabilities, I can see what you see.
I have access to desktop automation tools and can learn from demonstrations."""
    
    def get_human(self) -> str:
        return self.human
    
    def get_persona(self) -> str:
        return self.persona
    
    def set_human(self, content: str) -> bool:
        if len(content) <= self.max_chars_human:
            self.human = content
            return True
        return False
    
    def set_persona(self, content: str) -> bool:
        if len(content) <= self.max_chars_persona:
            self.persona = content
            return True
        return False
    
    def get_human_chars(self) -> tuple:
        return len(self.human), self.max_chars_human
    
    def get_persona_chars(self) -> tuple:
        return len(self.persona), self.max_chars_persona
    
    def to_prompt(self) -> str:
        return f"""### Core Memory - Human Context:
{self.human}

### Core Memory - Persona:
{self.persona}"""


class ArchivalMemory:
    """Letta-style archival memory for long-term storage."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory/archival")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.memories: List[Dict] = self._load_memories()
    
    def _load_memories(self) -> List[Dict]:
        archive_file = self.storage_path / "archival.json"
        if archive_file.exists():
            try:
                return json.loads(archive_file.read_text())
            except:
                return []
        return []
    
    def _save_memories(self):
        archive_file = self.storage_path / "archival.json"
        archive_file.write_text(json.dumps(self.memories, indent=2))
    
    def add(self, content: str, metadata: Optional[Dict] = None):
        memory = {
            "id": len(self.memories),
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "metadata": metadata or {}
        }
        self.memories.append(memory)
        self._save_memories()
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        # Simple keyword search
        query_lower = query.lower()
        results = [m for m in self.memories if query_lower in m["content"].lower()]
        return results[:limit]
    
    def get_all(self) -> List[Dict]:
        return self.memories
    
    def count(self) -> int:
        return len(self.memories)
    
    def delete(self, memory_id: int) -> bool:
        self.memories = [m for m in self.memories if m["id"] != memory_id]
        self._save_memories()
        return True


class ConversationMessage:
    """Represents a message in the conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # "user" or "agent"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.internal_reasoning = ""  # For agent reasoning display
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "reasoning": self.internal_reasoning
        }


class TextHandler:
    """Custom handler for redirecting logs to text widget."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')


class LettaStyleGUI:
    """Enhanced GUI with Letta-like specifications."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Humain - Letta-Style Agent")
        self.root.geometry("1400x900")
        
        # Initialize memory systems
        self.core_memory = CoreMemory()
        self.archival_memory = ArchivalMemory()
        self.demo_memory = DemonstrationMemory()
        self.episodic_memory = EpisodicMemory()
        self.memory_summarizer = MemorySummarizer()
        
        # Conversation history
        self.conversation: List[ConversationMessage] = []
        
        # Agent state
        self.current_models = []
        self.cancel_event = None
        self.agent_thread = None
        self.provider_health_status = "unknown"
        self.provider_health_message = ""
        self.token_count = 0
        self.max_tokens = 8192
        self.token_encoder = self._init_token_encoder()
        
        self._init_style()
        self.setup_ui()
        self._detect_initial_provider()
        self.load_models()

    def _init_token_encoder(self, model_name: str = "gpt-4"):
        """Initialize tiktoken encoder for accurate token counts."""
        if tiktoken is None:
            logger.warning("tiktoken not installed; using approximate token counts")
            return None
        try:
            return tiktoken.encoding_for_model(model_name)
        except Exception:
            try:
                return tiktoken.get_encoding("cl100k_base")
            except Exception as exc:
                logger.debug(f"Token encoder fallback failed: {exc}")
                return None

    def _count_tokens(self, text: str) -> int:
        """Return token count using encoder with safe fallback."""
        if not text:
            return 0
        if self.token_encoder:
            try:
                return len(self.token_encoder.encode(text))
            except Exception as exc:
                logger.debug(f"Token encoding error, using heuristic: {exc}")
        return int(len(text.split()) * 1.3)

    def _refresh_token_encoder(self, model_name: Optional[str] = None):
        """Refresh encoder when model selection changes."""
        if model_name:
            self.token_encoder = self._init_token_encoder(model_name)
        
    def _init_style(self):
        """Initialize modern color scheme."""
        # Letta-inspired palette
        bg = "#0f111a"           # Deep dark background
        panel = "#1a1d2e"        # Panel background
        panel_light = "#252837"  # Lighter panels
        input_bg = "#2d3148"     # Input fields
        accent = "#6366f1"       # Indigo accent
        accent_hover = "#4f46e5" # Darker indigo
        success = "#10b981"      # Green
        warning = "#f59e0b"      # Orange  
        error = "#ef4444"        # Red
        text = "#f3f4f6"         # Light text
        text_muted = "#9ca3af"   # Muted text
        border = "#374151"       # Borders
        
        self.root.configure(bg=bg)
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure styles
        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("Light.TFrame", background=panel_light)
        
        style.configure("TLabelframe", 
                       background=panel, 
                       foreground=text,
                       bordercolor=border,
                       borderwidth=1,
                       relief="solid")
        style.configure("TLabelframe.Label",
                       background=panel,
                       foreground=accent,
                       font=("Segoe UI", 10, "bold"),
                       padding=6)
        
        style.configure("TLabel",
                       background=panel,
                       foreground=text,
                       font=("Segoe UI", 9))
        style.configure("Muted.TLabel",
                       foreground=text_muted)
        
        style.configure("TButton",
                       background=accent,
                       foreground="#ffffff",
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"),
                       padding=8)
        style.map("TButton",
                 background=[("active", accent_hover)])
        
        style.configure("Success.TButton", background=success)
        style.map("Success.TButton", background=[("active", "#059669")])
        
        style.configure("TCombobox",
                       fieldbackground=input_bg,
                       background=input_bg,
                       foreground=text,
                       arrowcolor=accent)
        
        style.configure("TEntry",
                       fieldbackground=input_bg,
                       foreground=text,
                       bordercolor=border)
        
        style.configure("TCheckbutton",
                       background=panel,
                       foreground=text)
        
        self.colors = {
            "bg": bg,
            "panel": panel,
            "panel_light": panel_light,
            "input_bg": input_bg,
            "accent": accent,
            "accent_hover": accent_hover,
            "success": success,
            "warning": warning,
            "error": error,
            "text": text,
            "text_muted": text_muted,
            "border": border,
        }
    
    def setup_ui(self):
        """Setup the main UI with Letta-style layout."""
        # Main container with 3-column layout
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left sidebar - Agent Settings & Tools (300px)
        left_panel = ttk.Frame(main_container, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Center - Conversation/Simulator (expand)
        center_panel = ttk.Frame(main_container)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Right sidebar - Context Window (350px)
        right_panel = ttk.Frame(main_container, width=350)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Setup each panel
        self._setup_left_panel(left_panel)
        self._setup_center_panel(center_panel)
        self._setup_right_panel(right_panel)
    
    def _setup_left_panel(self, parent):
        """Setup left sidebar with agent settings."""
        # Agent Settings Header
        header = ttk.Label(parent, text="AGENT SETTINGS", 
                          font=("Segoe UI", 11, "bold"),
                          foreground=self.colors["accent"])
        header.pack(pady=(5, 10))
        
        # LLM Config
        llm_frame = ttk.LabelFrame(parent, text="LLM Configuration", padding="8")
        llm_frame.pack(fill=tk.X, pady=5)
        
        # Provider with health indicator
        prov_frame = ttk.Frame(llm_frame)
        prov_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(prov_frame, text="Provider:").pack(side=tk.LEFT, padx=2)
        
        self.health_canvas = tk.Canvas(prov_frame, width=10, height=10,
                                       bg=self.colors["panel"], highlightthickness=0)
        self.health_canvas.pack(side=tk.LEFT, padx=3)
        self.health_dot = self.health_canvas.create_oval(1, 1, 9, 9, fill="#666666", outline="")
        
        self.provider_var = tk.StringVar(value="ollama")
        provider_combo = ttk.Combobox(prov_frame, textvariable=self.provider_var,
                                     state="readonly", width=12)
        provider_combo['values'] = ["ollama", "openrouter", "letta"]
        provider_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        provider_combo.bind("<<ComboboxSelected>>", lambda e: self.load_models())
        
        # Model
        ttk.Label(llm_frame, text="Model:").pack(anchor="w", pady=(5, 2))
        self.model_var = tk.StringVar()
        model_combo = ttk.Combobox(llm_frame, textvariable=self.model_var, state="readonly")
        model_combo.pack(fill=tk.X, pady=2)
        self.model_combo = model_combo
        
        # API Key
        ttk.Label(llm_frame, text="API Key:").pack(anchor="w", pady=(5, 2))
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENROUTER_API_KEY", ""))
        api_entry = ttk.Entry(llm_frame, textvariable=self.api_key_var, show="*")
        api_entry.pack(fill=tk.X, pady=2)
        
        btn_frame = ttk.Frame(llm_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_models, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Set Key", command=self._set_env_api_key, width=10).pack(side=tk.LEFT, padx=2)
        
        # Agent Type
        agent_frame = ttk.LabelFrame(parent, text="Agent Configuration", padding="8")
        agent_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(agent_frame, text="Type:").pack(anchor="w", pady=2)
        self.agent_type_var = tk.StringVar(value="desktop_automation")
        agent_combo = ttk.Combobox(agent_frame, textvariable=self.agent_type_var,
                                   state="readonly", values=["desktop_automation", "memgpt_agent"])
        agent_combo.pack(fill=tk.X, pady=2)
        
        ttk.Label(agent_frame, text="Frequency:").pack(anchor="w", pady=(5, 2))
        self.freq_var = tk.IntVar(value=2)
        freq_scale = ttk.Scale(agent_frame, from_=1, to=10, variable=self.freq_var, orient=tk.HORIZONTAL)
        freq_scale.pack(fill=tk.X, pady=2)
        
        # System Instructions
        sys_frame = ttk.LabelFrame(parent, text="System Instructions", padding="8")
        sys_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.sys_inst_text = tk.Text(sys_frame, height=8, width=30,
                                    bg=self.colors["input_bg"],
                                    fg=self.colors["text"],
                                    wrap="word",
                                    font=("Segoe UI", 9))
        self.sys_inst_text.pack(fill=tk.BOTH, expand=True)
        self.sys_inst_text.insert("1.0", "Act as a desktop automation agent. Help users automate tasks using vision and reasoning.")
        
        ttk.Button(sys_frame, text="Configure", command=self._configure_system).pack(pady=5)
        
        # Tools (collapsed)
        tools_frame = ttk.LabelFrame(parent, text="Tools", padding="5")
        tools_frame.pack(fill=tk.X, pady=5)
        
        tool_label = ttk.Label(tools_frame, text="Tool Manager ▼", cursor="hand2",
                              foreground=self.colors["accent"])
        tool_label.pack(anchor="w")
        tool_label.bind("<Button-1>", lambda e: self._toggle_tools())
        
        self.tools_expanded = False
        self.tools_list_frame = ttk.Frame(tools_frame)
        
    def _setup_center_panel(self, parent):
        """Setup center panel with conversation/simulator."""
        # Tabs for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Agent Simulator Tab
        sim_frame = ttk.Frame(notebook)
        notebook.add(sim_frame, text="Agent Simulator")
        self._setup_simulator(sim_frame)
        
        # Logs Tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Execution Logs")
        self._setup_logs(log_frame)
        
        # Memory Tab
        mem_frame = ttk.Frame(notebook)
        notebook.add(mem_frame, text="Memory Management")
        self._setup_memory_tab(mem_frame)
    
    def _setup_simulator(self, parent):
        """Setup conversation simulator."""
        # Top controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Button(control_frame, text="▶ Run", command=self.run_conversation,
                  style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="■ Stop", command=self.stop_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="🎤 Voice", command=self.voice_to_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="🗑 Clear", command=self.clear_conversation).pack(side=tk.LEFT, padx=2)
        
        self.auto_advance_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Auto-advance", variable=self.auto_advance_var).pack(side=tk.LEFT, padx=5)
        
        # Conversation display
        conv_container = ttk.Frame(parent)
        conv_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.conv_text = scrolledtext.ScrolledText(conv_container,
                                                   bg=self.colors["bg"],
                                                   fg=self.colors["text"],
                                                   wrap="word",
                                                   font=("Segoe UI", 10),
                                                   padx=10,
                                                   pady=10,
                                                   state='disabled')
        self.conv_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for styling
        self.conv_text.tag_config("user", foreground="#60a5fa", font=("Segoe UI", 10, "bold"))
        self.conv_text.tag_config("agent", foreground="#34d399", font=("Segoe UI", 10, "bold"))
        self.conv_text.tag_config("reasoning", foreground=self.colors["text_muted"], font=("Segoe UI", 9, "italic"))
        self.conv_text.tag_config("timestamp", foreground=self.colors["text_muted"], font=("Segoe UI", 8))
        
        # Input area
        input_container = ttk.Frame(parent)
        input_container.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_container, text="👤 User", foreground="#60a5fa",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=2)
        
        input_frame = ttk.Frame(input_container)
        input_frame.pack(fill=tk.X)
        
        self.input_text = tk.Text(input_frame, height=3, width=50,
                                 bg=self.colors["input_bg"],
                                 fg=self.colors["text"],
                                 wrap="word",
                                 font=("Segoe UI", 10),
                                 relief="solid",
                                 borderwidth=1)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        btn_container = ttk.Frame(input_frame)
        btn_container.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(btn_container, text="▶ Send", command=self.send_message,
                  style="Success.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(btn_container, text="📋 Copy", command=self._copy_input).pack(fill=tk.X, pady=2)
    
    def _setup_logs(self, parent):
        """Setup execution logs."""
        self.log_area = scrolledtext.ScrolledText(parent,
                                                  state='disabled',
                                                  bg=self.colors["bg"],
                                                  fg=self.colors["text"],
                                                  font=("Consolas", 9),
                                                  padx=8,
                                                  pady=6)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Redirect logger
        logger.remove()
        logger.add(TextHandler(self.log_area), format="{time:HH:mm:ss} | {level} | {message}")
    
    def _setup_memory_tab(self, parent):
        """Setup memory management tab."""
        # Demo recording controls
        demo_frame = ttk.LabelFrame(parent, text="Demonstration Recording", padding="8")
        demo_frame.pack(fill=tk.X, padx=5, pady=5)
        
        control_row = ttk.Frame(demo_frame)
        control_row.pack(fill=tk.X, pady=2)
        
        self.is_recording = False
        self.record_btn = ttk.Button(control_row, text="⏺ Start Recording",
                                     command=self.toggle_recording)
        self.record_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(control_row, text="Name:").pack(side=tk.LEFT, padx=5)
        self.demo_name_var = tk.StringVar(value="demo_1")
        ttk.Entry(control_row, textvariable=self.demo_name_var, width=15).pack(side=tk.LEFT, padx=2)
        
        # Replay controls
        replay_row = ttk.Frame(demo_frame)
        replay_row.pack(fill=tk.X, pady=5)
        
        self.selected_demo_var = tk.StringVar()
        self.demo_combo = ttk.Combobox(replay_row, textvariable=self.selected_demo_var,
                                       width=20, state="readonly")
        self.demo_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(replay_row, text="↻ Refresh", command=self.refresh_demos).pack(side=tk.LEFT, padx=2)
        ttk.Button(replay_row, text="▶ Replay", command=self.replay_demo).pack(side=tk.LEFT, padx=2)
        ttk.Button(replay_row, text="🗑 Delete", command=self.delete_demo).pack(side=tk.LEFT, padx=2)
        
        # Memory settings
        settings_frame = ttk.LabelFrame(parent, text="Memory Settings", padding="8")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.episodic_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Episodic Memory",
                       variable=self.episodic_enabled,
                       command=self.toggle_episodic).pack(anchor="w", pady=2)
        
        self.overlay_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Visual Indicators",
                       variable=self.overlay_enabled).pack(anchor="w", pady=2)
        
        ttk.Label(settings_frame, text="Replay Speed:").pack(anchor="w", pady=(5, 2))
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(settings_frame, from_=0.5, to=2.0,
                               variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.pack(fill=tk.X, pady=2)
        
        # Initialize demos
        self.refresh_demos()
    
    def _setup_right_panel(self, parent):
        """Setup right sidebar with context window."""
        # Header with token count
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(header_frame, text="CONTEXT WINDOW",
                 font=("Segoe UI", 11, "bold"),
                 foreground=self.colors["accent"]).pack(side=tk.LEFT)
        
        self.token_label = ttk.Label(header_frame, text="0/8192 TOKENS",
                                    foreground=self.colors["text_muted"],
                                    font=("Segoe UI", 9))
        self.token_label.pack(side=tk.RIGHT)
        
        # Token usage bar
        token_canvas = tk.Canvas(parent, height=8, bg=self.colors["bg"],
                                highlightthickness=0)
        token_canvas.pack(fill=tk.X, pady=2)
        
        self.token_bar = token_canvas.create_rectangle(0, 0, 0, 8,
                                                       fill=self.colors["success"],
                                                       outline="")
        self.token_canvas = token_canvas
        
        # Tabs for Core/Archival Memory
        memory_notebook = ttk.Notebook(parent)
        memory_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Core Memory Tab
        core_frame = ttk.Frame(memory_notebook)
        memory_notebook.add(core_frame, text="Core Memory (2)")
        self._setup_core_memory(core_frame)
        
        # Archival Memory Tab
        archival_frame = ttk.Frame(memory_notebook)
        memory_notebook.add(archival_frame, text=f"Archival Memory ({self.archival_memory.count()})")
        self._setup_archival_memory(archival_frame)
        self.archival_tab_text = f"Archival Memory ({self.archival_memory.count()})"
        memory_notebook.tab(1, text=self.archival_tab_text)
        
        self.memory_notebook = memory_notebook
    
    def _setup_core_memory(self, parent):
        """Setup core memory blocks."""
        # Human block
        human_frame = ttk.LabelFrame(parent, text="👤 human", padding="8")
        human_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Char counter
        human_chars, human_max = self.core_memory.get_human_chars()
        self.human_char_label = ttk.Label(human_frame,
                                         text=f"{human_chars}/{human_max} CHARS",
                                         foreground=self.colors["text_muted"],
                                         font=("Segoe UI", 8))
        self.human_char_label.pack(anchor="e")
        
        self.human_text = scrolledtext.ScrolledText(human_frame, height=8,
                                                    bg=self.colors["input_bg"],
                                                    fg=self.colors["text"],
                                                    wrap="word",
                                                    font=("Segoe UI", 9))
        self.human_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.human_text.insert("1.0", self.core_memory.get_human())
        self.human_text.bind("<KeyRelease>", lambda e: self._update_human_chars())
        
        ttk.Button(human_frame, text="💾 Save", command=self._save_human_memory).pack()
        
        # Persona block
        persona_frame = ttk.LabelFrame(parent, text="🤖 persona", padding="8")
        persona_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        persona_chars, persona_max = self.core_memory.get_persona_chars()
        self.persona_char_label = ttk.Label(persona_frame,
                                           text=f"{persona_chars}/{persona_max} CHARS",
                                           foreground=self.colors["text_muted"],
                                           font=("Segoe UI", 8))
        self.persona_char_label.pack(anchor="e")
        
        self.persona_text = scrolledtext.ScrolledText(persona_frame, height=8,
                                                      bg=self.colors["input_bg"],
                                                      fg=self.colors["text"],
                                                      wrap="word",
                                                      font=("Segoe UI", 9))
        self.persona_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.persona_text.insert("1.0", self.core_memory.get_persona())
        self.persona_text.bind("<KeyRelease>", lambda e: self._update_persona_chars())
        
        ttk.Button(persona_frame, text="💾 Save", command=self._save_persona_memory).pack()
    
    def _setup_archival_memory(self, parent):
        """Setup archival memory display."""
        # Search
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.arch_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.arch_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(search_frame, text="🔍 Search",
                  command=self._search_archival).pack(side=tk.LEFT)
        
        # Memory list
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.arch_listbox = tk.Listbox(list_frame,
                                       bg=self.colors["input_bg"],
                                       fg=self.colors["text"],
                                       font=("Segoe UI", 9),
                                       selectbackground=self.colors["accent"])
        self.arch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.arch_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.arch_listbox.config(yscrollcommand=scrollbar.set)
        
        # Controls
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="+ Add", command=self._add_archival).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="👁 View", command=self._view_archival).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="🗑 Delete", command=self._delete_archival).pack(side=tk.LEFT, padx=2)
        
        self._refresh_archival_list()
    
    # Memory management methods
    def _update_human_chars(self):
        content = self.human_text.get("1.0", "end-1c")
        current_len = len(content)
        max_len = self.core_memory.max_chars_human
        self.human_char_label.config(text=f"{current_len}/{max_len} CHARS")
        
        if current_len > max_len:
            self.human_char_label.config(foreground=self.colors["error"])
        else:
            self.human_char_label.config(foreground=self.colors["text_muted"])
    
    def _update_persona_chars(self):
        content = self.persona_text.get("1.0", "end-1c")
        current_len = len(content)
        max_len = self.core_memory.max_chars_persona
        self.persona_char_label.config(text=f"{current_len}/{max_len} CHARS")
        
        if current_len > max_len:
            self.persona_char_label.config(foreground=self.colors["error"])
        else:
            self.persona_char_label.config(foreground=self.colors["text_muted"])
    
    def _save_human_memory(self):
        content = self.human_text.get("1.0", "end-1c")
        if self.core_memory.set_human(content):
            logger.success("Human memory updated")
        else:
            messagebox.showerror("Error", f"Content exceeds {self.core_memory.max_chars_human} characters")
    
    def _save_persona_memory(self):
        content = self.persona_text.get("1.0", "end-1c")
        if self.core_memory.set_persona(content):
            logger.success("Persona memory updated")
        else:
            messagebox.showerror("Error", f"Content exceeds {self.core_memory.max_chars_persona} characters")
    
    def _refresh_archival_list(self):
        """Refresh archival memory list."""
        self.arch_listbox.delete(0, tk.END)
        for mem in self.archival_memory.get_all():
            preview = mem["content"][:60] + "..." if len(mem["content"]) > 60 else mem["content"]
            self.arch_listbox.insert(tk.END, f"[{mem['id']}] {preview}")
        
        # Update tab label (if notebook exists)
        if hasattr(self, 'memory_notebook'):
            count = self.archival_memory.count()
            self.memory_notebook.tab(1, text=f"Archival Memory ({count})")
    
    def _search_archival(self):
        """Search archival memory."""
        query = self.arch_search_var.get().strip()
        if not query:
            self._refresh_archival_list()
            return
        
        results = self.archival_memory.search(query)
        self.arch_listbox.delete(0, tk.END)
        
        if results:
            for mem in results:
                preview = mem["content"][:60] + "..." if len(mem["content"]) > 60 else mem["content"]
                self.arch_listbox.insert(tk.END, f"[{mem['id']}] {preview}")
        else:
            self.arch_listbox.insert(tk.END, "No results found")
    
    def _add_archival(self):
        """Add new archival memory."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Archival Memory")
        dialog.geometry("500x300")
        dialog.configure(bg=self.colors["panel"])
        
        ttk.Label(dialog, text="Content:").pack(anchor="w", padx=10, pady=5)
        
        text_widget = tk.Text(dialog, height=10,
                             bg=self.colors["input_bg"],
                             fg=self.colors["text"],
                             wrap="word")
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def save():
            content = text_widget.get("1.0", "end-1c").strip()
            if content:
                self.archival_memory.add(content)
                self._refresh_archival_list()
                logger.success("Memory added to archival")
                dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
    
    def _view_archival(self):
        """View selected archival memory."""
        selection = self.arch_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        memories = self.archival_memory.get_all()
        if idx < len(memories):
            mem = memories[idx]
            messagebox.showinfo(f"Memory #{mem['id']}", 
                              f"Timestamp: {mem['timestamp']}\n\n{mem['content']}")
    
    def _delete_archival(self):
        """Delete selected archival memory."""
        selection = self.arch_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        memories = self.archival_memory.get_all()
        if idx < len(memories):
            mem = memories[idx]
            if messagebox.askyesno("Confirm", f"Delete memory #{mem['id']}?"):
                self.archival_memory.delete(mem["id"])
                self._refresh_archival_list()
                logger.info(f"Memory #{mem['id']} deleted")
    
    def _update_token_display(self):
        """Update token count display and progress bar."""
        self.token_label.config(text=f"{self.token_count}/{self.max_tokens} TOKENS")
        
        # Update progress bar
        width = self.token_canvas.winfo_width()
        progress = min(1.0, self.token_count / self.max_tokens)
        bar_width = int(width * progress)
        
        # Color based on usage
        if progress < 0.7:
            color = self.colors["success"]
        elif progress < 0.9:
            color = self.colors["warning"]
        else:
            color = self.colors["error"]
        
        self.token_canvas.coords(self.token_bar, 0, 0, bar_width, 8)
        self.token_canvas.itemconfig(self.token_bar, fill=color)
    
    # Conversation methods
    def add_message(self, role: str, content: str, reasoning: str = ""):
        """Add message to conversation display."""
        msg = ConversationMessage(role, content)
        msg.internal_reasoning = reasoning
        self.conversation.append(msg)
        
        self.conv_text.configure(state='normal')
        
        # Timestamp
        timestamp = msg.timestamp.strftime("%H:%M:%S")
        self.conv_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Role and content
        if role == "user":
            self.conv_text.insert(tk.END, "👤 USER\n", "user")
            self.conv_text.insert(tk.END, f"{content}\n\n")
        else:  # agent
            self.conv_text.insert(tk.END, "🤖 AGENT\n", "agent")
            if reasoning:
                self.conv_text.insert(tk.END, f"💭 Reasoning\n", "agent")
                self.conv_text.insert(tk.END, f"{reasoning}\n\n", "reasoning")
            self.conv_text.insert(tk.END, f"{content}\n\n")
        
        self.conv_text.see(tk.END)
        self.conv_text.configure(state='disabled')
        
        # Update token count using encoder (content + reasoning)
        self.token_count += self._count_tokens(content)
        if reasoning:
            self.token_count += self._count_tokens(reasoning)
        self._update_token_display()
    
    def send_message(self):
        """Send user message."""
        content = self.input_text.get("1.0", "end-1c").strip()
        if not content:
            return
        
        self.add_message("user", content)
        self.input_text.delete("1.0", tk.END)
        
        # Process message (would trigger agent)
        # For now, just acknowledge
        threading.Thread(target=self._process_message, args=(content,), daemon=True).start()
    
    def _process_message(self, user_input: str):
        """Process user message and generate response."""
        # This is where you'd call the actual agent
        # For now, placeholder
        import time
        time.sleep(1)
        
        reasoning = "I should analyze what the user wants and determine the best approach."
        response = f"I understand you want to: {user_input}. Let me help with that."
        
        self.add_message("agent", response, reasoning)
    
    def run_conversation(self):
        """Run the agent conversation."""
        user_input = self.input_text.get("1.0", "end-1c").strip()
        if user_input:
            self.send_message()
        else:
            logger.warning("Please enter a message first")
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation.clear()
        self.conv_text.configure(state='normal')
        self.conv_text.delete("1.0", tk.END)
        self.conv_text.configure(state='disabled')
        self.token_count = 0
        self._update_token_display()
        logger.info("Conversation cleared")
    
    # LLM methods (similar to original)
    def load_models(self):
        provider = self.provider_var.get()
        if provider == "ollama":
            self._load_ollama_models()
        elif provider == "openrouter":
            self._load_openrouter_models()
        elif provider == "letta":
            self._load_letta_models()
    
    def _load_ollama_models(self):
        try:
            provider = OllamaProvider()
            models_meta = provider.list_models()
            model_names = [m.get("name") or m.get("model") or m.get("id") 
                          for m in models_meta if m.get("name") or m.get("model") or m.get("id")]
            
            if not model_names:
                raise RuntimeError("No models found")
            
            self.current_models = model_names
            self.apply_filter()
            self._update_health_indicator("healthy", "Ollama: Connected")
        except Exception as e:
            logger.warning(f"Ollama unavailable: {e}")
            self._update_health_indicator("unhealthy", f"Ollama: {str(e)[:50]}")
            self.provider_var.set("openrouter")
            self._load_openrouter_models()
    
    def _load_openrouter_models(self):
        config = load_config()
        base_url = config.get("llm", {}).get("openrouter", {}).get("base_url", "https://openrouter.ai/api/v1")
        api_key = self.api_key_var.get().strip() or os.environ.get("OPENROUTER_API_KEY", "")
        
        fallback_models = [
            "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/qwen/qwen-2-7b-instruct",
        ]
        
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(f"{base_url.rstrip('/')}/models",
                                headers={"Authorization": f"Bearer {api_key}"} if api_key else {})
                resp.raise_for_status()
                models = [item.get("id") for item in resp.json().get("data", []) if item.get("id")]
                
                if models:
                    self.current_models = models
                    self.apply_filter()
                    self._update_health_indicator("healthy", "OpenRouter: Connected")
                    return
        except Exception as e:
            logger.warning(f"OpenRouter fetch failed: {e}")
        
        self.current_models = fallback_models
        self.apply_filter()
        self._update_health_indicator("healthy" if api_key else "unhealthy",
                                     "OpenRouter: Using fallback" if api_key else "No API key")
    
    def _load_letta_models(self):
        self.current_models = [
            "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/qwen/qwen-2-7b-instruct",
        ]
        self.apply_filter()
        
        api_key = self.api_key_var.get().strip() or os.environ.get("LETTA_API_KEY", "")
        self._update_health_indicator("healthy" if api_key else "unhealthy",
                                     "Letta: " + ("Configured" if api_key else "No API key"))
    
    def apply_filter(self):
        models = getattr(self, "current_models", [])
        if models:
            self.model_combo['values'] = models
            self.model_combo.set(models[0])
            self._refresh_token_encoder(self.model_var.get())
    
    def _detect_initial_provider(self):
        try:
            provider = OllamaProvider()
            if provider.list_models():
                self.provider_var.set("ollama")
                return
        except:
            pass
        
        if os.environ.get("OPENROUTER_API_KEY"):
            self.provider_var.set("openrouter")
    
    def _update_health_indicator(self, status: str, message: str):
        self.provider_health_status = status
        self.provider_health_message = message
        
        colors = {
            "healthy": "#10b981",
            "unhealthy": "#ef4444",
            "unknown": "#6b7280"
        }
        
        self.health_canvas.itemconfig(self.health_dot, fill=colors.get(status, colors["unknown"]))
    
    # Utility methods
    def _set_env_api_key(self):
        key = self.api_key_var.get().strip()
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
            logger.success("API key set in environment")
    
    def _configure_system(self):
        messagebox.showinfo("System Instructions", "System instructions configured")
    
    def _toggle_tools(self):
        if self.tools_expanded:
            self.tools_list_frame.pack_forget()
            self.tools_expanded = False
        else:
            self.tools_list_frame.pack(fill=tk.X, pady=5)
            self.tools_expanded = True
    
    def _copy_input(self):
        content = self.input_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
    
    def voice_to_text(self):
        if sr is None:
            logger.error("speech_recognition not installed")
            return
        
        def capture():
            try:
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    logger.info("Listening...")
                    audio = recognizer.listen(source, timeout=5)
                    text = recognizer.recognize_google(audio)
                    self.input_text.delete("1.0", tk.END)
                    self.input_text.insert("1.0", text)
                    logger.success(f"Voice captured: {text}")
            except Exception as e:
                logger.error(f"Voice capture failed: {e}")
        
        threading.Thread(target=capture, daemon=True).start()
    
    def start_task(self):
        logger.info("Task started (placeholder)")
    
    def stop_task(self):
        logger.info("Task stopped")
    
    # Demo/memory methods (from original)
    def toggle_recording(self):
        if not self.is_recording:
            self.demo_memory.start_recording()
            self.is_recording = True
            self.record_btn.configure(text="⏹ Stop Recording")
            logger.info("Recording started")
        else:
            actions = self.demo_memory.stop_recording()
            self.is_recording = False
            self.record_btn.configure(text="⏺ Start Recording")
            
            demo_name = self.demo_name_var.get().strip()
            if demo_name and actions:
                self.demo_memory.save_demonstration(demo_name, actions)
                logger.success(f"Saved '{demo_name}' with {len(actions)} actions")
                self.refresh_demos()
    
    def refresh_demos(self):
        demos = self.demo_memory.list_demonstrations()
        demo_names = [d['name'] for d in demos]
        self.demo_combo['values'] = demo_names
        if demo_names:
            self.demo_combo.set(demo_names[0])
    
    def replay_demo(self):
        demo_name = self.selected_demo_var.get()
        if not demo_name:
            return
        
        def replay_thread():
            try:
                results = self.demo_memory.replay_demonstration(demo_name, speed=self.speed_var.get())
                logger.success(f"Replayed: {len(results)} actions")
            except Exception as e:
                logger.error(f"Replay failed: {e}")
        
        threading.Thread(target=replay_thread, daemon=True).start()
    
    def delete_demo(self):
        demo_name = self.selected_demo_var.get()
        if demo_name and self.demo_memory.delete_demonstration(demo_name):
            logger.success(f"Deleted '{demo_name}'")
            self.refresh_demos()
    
    def toggle_episodic(self):
        enabled = self.episodic_enabled.get()
        self.episodic_memory.enable_recall = enabled
        logger.info(f"Episodic memory {'enabled' if enabled else 'disabled'}")


if __name__ == "__main__":
    root = tk.Tk()
    app = LettaStyleGUI(root)
    root.mainloop()
