import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import os
from pathlib import Path
from typing import List
import ollama
import httpx
from loguru import logger

# Optional voice input
try:
    import speech_recognition as sr
except ImportError:  # Voice input stays optional
    sr = None

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

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

class TextHandler:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

class DigitalHumainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Humain - Desktop Automation")
        self.root.geometry("1200x850")
        self._init_style()
        self.current_models = []
        
        # Initialize memory systems
        self.demo_memory = DemonstrationMemory()
        self.episodic_memory = EpisodicMemory()
        self.memory_summarizer = MemorySummarizer()
        
        self.setup_ui()
        self.load_models()

    def _init_style(self):
        # Dark futuristic palette
        bg = "#0f1116"
        panel = "#161925"
        accent = "#5ee7ff"
        text = "#e6eef8"
        subdued = "#8aa2c2"

        self.root.configure(bg=bg)
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=panel, foreground=text, bordercolor=accent, relief="solid")
        style.configure("TLabelframe.Label", background=panel, foreground=text, padding=4)
        style.configure("TLabel", background=panel, foreground=text)
        style.configure("TButton", background=panel, foreground=text, borderwidth=0, focusthickness=3, focuscolor=accent)
        style.map("TButton", background=[("active", "#1f2538")])
        style.configure("TCombobox", fieldbackground=panel, background=panel, foreground=text, arrowcolor=accent, selectbackground="#243047", selectforeground=text)
        style.configure("TEntry", fieldbackground=panel, foreground=text, bordercolor=accent, lightcolor=panel, darkcolor=panel)
        style.configure("Vertical.TScrollbar", gripcount=0, background=panel, darkcolor=panel, lightcolor=panel, troughcolor=bg, bordercolor=bg, arrowcolor=accent)

        self.colors = {
            "bg": bg,
            "panel": panel,
            "accent": accent,
            "text": text,
            "subdued": subdued,
        }
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Provider & Model Selection
        model_frame = ttk.LabelFrame(main_frame, text="LLM Configuration", padding="8")
        model_frame.pack(fill=tk.X, pady=8)

        # Make columns stretch for cleaner layout
        model_frame.columnconfigure(1, weight=1)
        model_frame.columnconfigure(3, weight=1)

        ttk.Label(model_frame, text="Provider:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.provider_var = tk.StringVar(value="ollama")
        self.provider_combo = ttk.Combobox(model_frame, textvariable=self.provider_var, state="readonly")
        self.provider_combo['values'] = ["ollama", "openrouter", "letta"]
        self.provider_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.provider_combo.bind("<<ComboboxSelected>>", lambda _e: self.load_models())

        ttk.Label(model_frame, text="Model:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly")
        self.model_combo.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        ttk.Button(model_frame, text="Refresh Models", command=self.load_models).grid(row=0, column=4, padx=5, pady=2)

        ttk.Label(model_frame, text="API Key (OpenRouter/Letta):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENROUTER_API_KEY", ""))
        self.api_key_entry = ttk.Entry(model_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        ttk.Button(model_frame, text="Set Env", command=self._set_env_api_key).grid(row=1, column=4, padx=5, pady=2)

        ttk.Label(model_frame, text="Filter:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(model_frame, textvariable=self.filter_var)
        self.filter_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.filter_entry.bind("<KeyRelease>", lambda _e: self.apply_filter())

        self.free_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(model_frame, text="Free only", variable=self.free_only, command=self.apply_filter).grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Button(model_frame, text="Apply Filter", command=self.apply_filter).grid(row=2, column=3, padx=5, pady=2)
        
        task_frame = ttk.LabelFrame(main_frame, text="Task", padding="8")
        task_frame.pack(fill=tk.X, pady=8)
        self.task_text = tk.Text(task_frame, height=4, width=50, bg=self.colors["panel"], fg=self.colors["text"], insertbackground=self.colors["accent"], highlightthickness=0, relief="flat", wrap="word")
        self.task_text.pack(fill=tk.X, padx=5, pady=5)
        self.task_text.insert("1.0", "Go to notepad and write a letter to Steve Jobs in 10 words")
        
        # Controls
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = ttk.Button(control_frame, text="Run Task", command=self.start_task)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Voice Input", command=self.voice_to_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        # Recording & Memory Controls
        memory_frame = ttk.LabelFrame(main_frame, text="Recording & Memory", padding="8")
        memory_frame.pack(fill=tk.X, pady=8)
        
        # Recording controls
        record_frame = ttk.Frame(memory_frame)
        record_frame.pack(side=tk.LEFT, padx=10)
        
        self.is_recording = False
        self.record_btn = ttk.Button(record_frame, text="Start Recording", command=self.toggle_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(record_frame, text="Demo Name:").pack(side=tk.LEFT, padx=5)
        self.demo_name_var = tk.StringVar(value="demo_1")
        ttk.Entry(record_frame, textvariable=self.demo_name_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Replay controls
        replay_frame = ttk.Frame(memory_frame)
        replay_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(replay_frame, text="Replay:").pack(side=tk.LEFT, padx=5)
        self.selected_demo_var = tk.StringVar()
        self.demo_combo = ttk.Combobox(replay_frame, textvariable=self.selected_demo_var, width=15, state="readonly")
        self.demo_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(replay_frame, text="Refresh", command=self.refresh_demos).pack(side=tk.LEFT, padx=2)
        ttk.Button(replay_frame, text="Replay", command=self.replay_demo).pack(side=tk.LEFT, padx=2)
        ttk.Button(replay_frame, text="Dry Run", command=self.dry_run_demo).pack(side=tk.LEFT, padx=2)
        ttk.Button(replay_frame, text="Delete", command=self.delete_demo).pack(side=tk.LEFT, padx=2)
        
        # Memory settings
        mem_settings_frame = ttk.Frame(memory_frame)
        mem_settings_frame.pack(side=tk.LEFT, padx=10)
        
        self.episodic_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(mem_settings_frame, text="Episodic Memory", variable=self.episodic_enabled, 
                       command=self.toggle_episodic).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mem_settings_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(mem_settings_frame, from_=0.5, to=2.0, variable=self.speed_var, 
                               orient=tk.HORIZONTAL, length=100)
        speed_scale.pack(side=tk.LEFT, padx=5)
        
        self.safety_pause_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mem_settings_frame, text="Safety Pause", variable=self.safety_pause_var).pack(side=tk.LEFT, padx=5)
        
        # Initialize demo list
        self.refresh_demos()
        
        # Logs
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=20, bg=self.colors["panel"], fg=self.colors["text"], insertbackground=self.colors["accent"], highlightthickness=0, relief="flat")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Redirect logger
        logger.remove()
        logger.add(TextHandler(self.log_area), format="{time:HH:mm:ss} | {level} | {message}")

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
            response = ollama.list()
            if hasattr(response, 'models'):
                model_names = [m.model for m in response.models]
            else:
                model_names = [m['model'] for m in response['models']]
            self.current_models = model_names
            self.apply_filter()
        except Exception as e:
            logger.error(f"Failed to load Ollama models: {e}")
            self.model_combo['values'] = ["Error loading models"]

    def _load_openrouter_models(self):
        config = load_config()
        base_url = config.get("llm", {}).get("openrouter", {}).get("base_url", "https://openrouter.ai/api/v1")
        api_key = self.api_key_var.get().strip() or os.environ.get("OPENROUTER_API_KEY", "")

        fallback_models: List[str] = [
            "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/qwen/qwen-2-7b-instruct",
            "openrouter/deepseek/deepseek-chat",
        ]

        try:
            url = f"{base_url.rstrip('/')}/models"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            with httpx.Client(timeout=20) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json().get("data", [])
                models = [item.get("id") for item in data if item.get("id")]
                if models:
                    self.current_models = models
                    self.apply_filter()
                    return
        except Exception as e:
            logger.warning(f"OpenRouter model fetch failed, using fallback list: {e}")

        self.current_models = fallback_models
        self.apply_filter()

    def _load_letta_models(self):
        # Letta uses server-side model selection; we surface a safe default list (free-first)
        cfg = load_config()
        default_model = cfg.get("llm", {}).get("letta", {}).get("default_model", "openrouter/nvidia/nemotron-nano-12b-v2-vl:free")
        self.current_models = [
            "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/amazon/nova-2-lite-v1:free",
            "openrouter/qwen/qwen-2-7b-instruct",
            "openrouter/deepseek/deepseek-chat",
        ]
        # Put configured default first if present
        if default_model in self.current_models:
            self.current_models.remove(default_model)
            self.current_models.insert(0, default_model)
        self.apply_filter()

    def apply_filter(self):
        models = getattr(self, "current_models", [])
        query = self.filter_var.get().lower()
        free_only = self.free_only.get()

        def match(m: str) -> bool:
            if free_only and "free" not in m.lower():
                return False
            if query and query not in m.lower():
                return False
            return True

        filtered = [m for m in models if match(m)]
        if not filtered and models:
            filtered = models  # fallback to full list if filter empty
        self.model_combo['values'] = filtered
        if filtered:
            self.model_combo.set(filtered[0])

    def clear_logs(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')

    def start_task(self):
        task = self.task_text.get("1.0", tk.END).strip()
        model = self.model_var.get()
        provider = self.provider_var.get()
        
        if not task:
            logger.warning("Please enter a task")
            return
            
        if not model:
            logger.warning("Please select a model")
            return
            
        self.run_btn.configure(state='disabled')
        threading.Thread(target=self.run_agent, args=(task, model, provider), daemon=True).start()

    def run_agent(self, task, model, provider):
        try:
            logger.info(f"Starting task with provider={provider}, model={model}")
            
            # Initialize components
            config = load_config()
            llm = self._build_llm(provider, model, config)
            
            screen_analyzer = ScreenAnalyzer(
                save_screenshots=True,
                screenshot_dir="./screenshots"
            )
            
            gui_actions = GUIActions(pause=1.0)  # Slower for safety
            
            tool_registry = ToolRegistry()
            tool_registry.register(FileReadTool())
            tool_registry.register(FileWriteTool())
            
            agent_config = AgentConfig(
                name="gui_agent",
                role=AgentRole.EXECUTOR,
                model=model,
                max_iterations=15
            )
            
            agent = DesktopAutomationAgent(
                config=agent_config,
                llm_provider=llm,
                screen_analyzer=screen_analyzer,
                gui_actions=gui_actions,
                tool_registry=tool_registry
            )
            
            engine = AgentEngine(agent)
            engine.build_graph()
            
            # Retrieve relevant past episodes if enabled
            if self.episodic_memory.enable_recall:
                relevant_episodes = self.episodic_memory.retrieve_relevant(task, top_k=3)
                if relevant_episodes:
                    logger.info(f"Retrieved {len(relevant_episodes)} relevant past episodes")
                    for ep in relevant_episodes:
                        logger.debug(f"  - Episode {ep.id}: {ep.observation[:50]}...")
            
            result = engine.run(task, recursion_limit=15)
            
            # Store episode in episodic memory if enabled
            if self.episodic_memory.enable_recall and result.get('history'):
                for step in result['history']:
                    self.episodic_memory.add_episode(
                        observation=step.get('observation', ''),
                        reasoning=step.get('reasoning', ''),
                        action=step.get('action', {}),
                        result=str(step.get('action', {}).get('success', False)),
                        metadata={'task': task, 'model': model, 'provider': provider}
                    )
            
            if result['error']:
                logger.error(f"Task failed: {result['error']}")
            else:
                logger.success("Task completed successfully!")
                
                # Log episodic memory stats
                if self.episodic_memory.enable_recall:
                    stats = self.episodic_memory.get_stats()
                    logger.info(f"Episodic memory: {stats['total_episodes']} episodes stored")
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state='normal'))

    def _build_llm(self, provider: str, model: str, config: dict):
        if provider == "openrouter":
            or_cfg = config.get("llm", {}).get("openrouter", {})
            api_key = self.api_key_var.get().strip() or os.environ.get("OPENROUTER_API_KEY", "")
            if not api_key:
                raise RuntimeError("OPENROUTER_API_KEY is missing. Set it in the field or environment.")
            return OpenRouterProvider(
                model=model,
                api_key=api_key,
                base_url=or_cfg.get("base_url", "https://openrouter.ai/api/v1"),
                timeout=or_cfg.get("timeout", 120),
                referer=or_cfg.get("referer"),
                site_url=or_cfg.get("site_url"),
            )
        if provider == "letta":
            let_cfg = config.get("llm", {}).get("letta", {})
            api_key = self.api_key_var.get().strip() or os.environ.get("LETTA_API_KEY", "")
            agent_id = let_cfg.get("agent_id") or os.environ.get("LETTA_AGENT_ID", "")
            if not api_key or not agent_id:
                raise RuntimeError("Letta requires LETTA_API_KEY and agent_id. Fill the key field and set LETTA_AGENT_ID env or config.")
            return LettaProvider(
                agent_id=agent_id,
                api_key=api_key,
                base_url=let_cfg.get("base_url", "https://api.letta.ai"),
                timeout=let_cfg.get("timeout", 120),
                model=model,
            )

        # Default to Ollama
        return OllamaProvider(
            model=model,
            base_url=config.get("llm", {}).get("base_url", "http://localhost:11434"),
            timeout=config.get("llm", {}).get("timeout", 300)
        )

    def _set_env_api_key(self):
        key = self.api_key_var.get().strip()
        if not key:
            logger.warning("No API key provided")
            return
        os.environ["OPENROUTER_API_KEY"] = key
        logger.success("OPENROUTER_API_KEY set for this session")

    def voice_to_text(self):
        if sr is None:
            logger.error("speech_recognition not installed. Run: pip install SpeechRecognition pyaudio")
            return
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                logger.info("Listening... (speak now)")
                audio = recognizer.listen(source, phrase_time_limit=10)
            text = recognizer.recognize_google(audio, language="en-US")
            if text:
                self.task_text.delete("1.0", tk.END)
                self.task_text.insert("1.0", text)
                logger.info(f"Voice captured: {text}")
        except Exception as e:
            logger.error(f"Voice capture failed: {e}")
    
    def toggle_recording(self):
        """Toggle recording on/off."""
        if not self.is_recording:
            # Start recording
            self.demo_memory.start_recording()
            self.is_recording = True
            self.record_btn.configure(text="Stop Recording")
            logger.info("Recording started - perform actions now")
        else:
            # Stop recording
            actions = self.demo_memory.stop_recording()
            self.is_recording = False
            self.record_btn.configure(text="Start Recording")
            
            # Save the recording
            demo_name = self.demo_name_var.get().strip()
            if demo_name and actions:
                self.demo_memory.save_demonstration(demo_name, actions)
                logger.success(f"Recording saved as '{demo_name}' with {len(actions)} actions")
                self.refresh_demos()
            else:
                logger.warning("No demo name provided or no actions recorded")
    
    def refresh_demos(self):
        """Refresh the list of available demonstrations."""
        demos = self.demo_memory.list_demonstrations()
        demo_names = [demo['name'] for demo in demos]
        self.demo_combo['values'] = demo_names
        if demo_names:
            self.demo_combo.set(demo_names[0])
        logger.debug(f"Refreshed demo list: {len(demo_names)} demonstrations")
    
    def replay_demo(self):
        """Replay the selected demonstration."""
        demo_name = self.selected_demo_var.get()
        if not demo_name:
            logger.warning("No demonstration selected")
            return
        
        speed = self.speed_var.get()
        safety_pause = self.safety_pause_var.get()
        
        def replay_thread():
            try:
                results = self.demo_memory.replay_demonstration(
                    demo_name,
                    speed=speed,
                    dry_run=False,
                    safety_pause=safety_pause
                )
                logger.success(f"Replay completed: {len(results)} actions executed")
            except Exception as e:
                logger.error(f"Replay failed: {e}")
        
        threading.Thread(target=replay_thread, daemon=True).start()
    
    def dry_run_demo(self):
        """Perform a dry run of the selected demonstration."""
        demo_name = self.selected_demo_var.get()
        if not demo_name:
            logger.warning("No demonstration selected")
            return
        
        results = self.demo_memory.replay_demonstration(
            demo_name,
            dry_run=True,
            safety_pause=False
        )
        
        logger.info(f"DRY RUN for '{demo_name}':")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['action']}: {result['params']}")
    
    def delete_demo(self):
        """Delete the selected demonstration."""
        demo_name = self.selected_demo_var.get()
        if not demo_name:
            logger.warning("No demonstration selected")
            return
        
        if self.demo_memory.delete_demonstration(demo_name):
            logger.success(f"Demonstration '{demo_name}' deleted")
            self.refresh_demos()
        else:
            logger.error(f"Failed to delete demonstration '{demo_name}'")
    
    def toggle_episodic(self):
        """Toggle episodic memory on/off."""
        enabled = self.episodic_enabled.get()
        self.episodic_memory.enable_recall = enabled
        logger.info(f"Episodic memory {'enabled' if enabled else 'disabled'}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalHumainGUI(root)
    root.mainloop()
